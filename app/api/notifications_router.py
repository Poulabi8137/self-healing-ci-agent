"""Notifications API router — notification history, settings."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth.dependencies import get_current_jwt_user
from app.database.db import SessionLocal
from app.database.models import Notification, NotificationSetting, User

router = APIRouter()


class SettingsUpdate(BaseModel):
    email_enabled: bool | None = None
    slack_enabled: bool | None = None


@router.get("/notifications")
async def get_notifications(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_jwt_user),
):
    """Return notification history for the authenticated user."""
    db = SessionLocal()
    try:
        query = db.query(Notification).filter(Notification.user_id == user.id)
        total = query.count()
        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "notifications": [
                {
                    "id": n.id,
                    "channel_type": n.channel_type,
                    "event_type": n.event_type,
                    "status": n.status,
                    "recipient": n.recipient,
                    "subject": n.subject,
                    "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
                    "failure_reason": n.failure_reason,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notifications
            ],
        }
    finally:
        db.close()


@router.get("/notifications/settings")
async def get_notification_settings(
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """Return notification preferences for the authenticated user."""
    db = SessionLocal()
    try:
        settings = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
        if not settings:
            settings = NotificationSetting(user_id=user.id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return {
            "email_enabled": settings.email_enabled,
            "slack_enabled": settings.slack_enabled,
        }
    finally:
        db.close()


@router.put("/notifications/settings")
async def update_notification_settings(
    body: SettingsUpdate,
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """Update notification preferences for the authenticated user."""
    db = SessionLocal()
    try:
        settings = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
        if not settings:
            settings = NotificationSetting(user_id=user.id)
            db.add(settings)

        if body.email_enabled is not None:
            settings.email_enabled = body.email_enabled
        if body.slack_enabled is not None:
            settings.slack_enabled = body.slack_enabled

        settings.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(settings)

        return {
            "email_enabled": settings.email_enabled,
            "slack_enabled": settings.slack_enabled,
        }
    finally:
        db.close()
