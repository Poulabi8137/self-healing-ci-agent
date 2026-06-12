"""Notification dispatcher — subscribes to investigation_events, routes to email/slack."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.database.db import SessionLocal
from app.database.models import Notification, NotificationSetting, SlackWorkspace, User
from app.services.email_service import build_email_content, send_email_async
from app.services.slack_service import build_slack_message, send_slack_message

logger = logging.getLogger(__name__)

# Event types we care about for notifications
NOTIFIABLE_EVENTS = {
    "investigation_started",
    "root_cause_identified",
    "fix_generated",
    "validation_completed",
    "pr_created",
    "workflow_failed",
}


def _get_recipient_users(db, event_type: str, data: dict[str, Any]) -> list[User]:
    """Determine which users should receive a notification for this event."""
    inv_id = data.get("investigation_id")
    repo = data.get("repository", data.get("repo", ""))

    users = db.query(User).filter(User.role.in_(["admin", "member"])).all()

    if inv_id:
        from app.database.models import Investigation, Repository, GitHubInstallation
        investigation = db.query(Investigation).filter(Investigation.id == inv_id).first()
        if investigation:
            repo_obj = db.query(Repository).filter(Repository.id == investigation.repository_id).first()
            if repo_obj and repo_obj.github_installation_id:
                inst = db.query(GitHubInstallation).filter(GitHubInstallation.id == repo_obj.github_installation_id).first()
                if inst:
                    owner = db.query(User).filter(User.id == inst.user_id).first()
                    if owner and owner not in users:
                        users.append(owner)

    return users


def _get_user_email(user: User) -> str | None:
    if user.email:
        return user.email
    if user.github_email:
        return user.github_email
    return None


async def process_event(event_type: str, data: dict[str, Any]) -> None:
    """Process an investigation event and dispatch notifications."""
    if event_type not in NOTIFIABLE_EVENTS:
        return

    db = SessionLocal()
    try:
        users = _get_recipient_users(db, event_type, data)
        tasks = []
        for user in users:
            settings = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
            if not settings:
                settings = NotificationSetting(user_id=user.id)
                db.add(settings)
                db.commit()

            # Email notification
            if settings.email_enabled:
                email = _get_user_email(user)
                if email:
                    tasks.append(_dispatch_email(db, user.id, email, event_type, data))

            # Slack notification
            if settings.slack_enabled:
                workspace = db.query(SlackWorkspace).filter(SlackWorkspace.user_id == user.id).first()
                if workspace and workspace.selected_channel_id:
                    tasks.append(_dispatch_slack(db, user.id, workspace, event_type, data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error("Notification dispatch error: %s", str(e))
    finally:
        db.close()


async def _dispatch_email(db, user_id: int, email: str, event_type: str, data: dict[str, Any]) -> None:
    """Build and send an email notification, persisting the result."""
    content = build_email_content(event_type, data)

    record = Notification(
        user_id=user_id,
        channel_type="email",
        event_type=event_type,
        status="pending",
        recipient=email,
        subject=content["subject"],
        body=content["text"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    success, error = await send_email_async(
        to_email=email,
        subject=content["subject"],
        html_body=content["html"],
        text_body=content["text"],
    )

    if success:
        record.status = "sent"
        record.delivered_at = datetime.now(timezone.utc)
    else:
        record.status = "failed"
        record.failure_reason = error

    db.commit()
    logger.info("Email notification %s for user %d (event=%s)", record.status, user_id, event_type)


async def _dispatch_slack(db, user_id: int, workspace: SlackWorkspace, event_type: str, data: dict[str, Any]) -> None:
    """Build and send a Slack notification, persisting the result."""
    message = build_slack_message(event_type, data)
    channel_name = workspace.selected_channel_name or workspace.selected_channel_id or "unknown"

    record = Notification(
        user_id=user_id,
        channel_type="slack",
        event_type=event_type,
        status="pending",
        recipient=f"{workspace.workspace_name}/#{channel_name}",
        subject=message.get("text", ""),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    success, error = await send_slack_message(
        access_token=workspace.access_token,
        channel=workspace.selected_channel_id,
        message=message,
    )

    if success:
        record.status = "sent"
        record.delivered_at = datetime.now(timezone.utc)
    else:
        record.status = "failed"
        record.failure_reason = error

    db.commit()
    logger.info("Slack notification %s for user %d (event=%s)", record.status, user_id, event_type)
