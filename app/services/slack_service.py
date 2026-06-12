"""Slack integration service — OAuth connect/disconnect, channel listing, messaging."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"

EVENT_ICONS = {
    "investigation_started": "🔍",
    "root_cause_identified": "🕵️",
    "fix_generated": "🔧",
    "validation_completed": "✅",
    "pr_created": "🎉",
    "workflow_failed": "❌",
}

EVENT_COLORS = {
    "investigation_started": "#6b7280",
    "root_cause_identified": "#f59e0b",
    "fix_generated": "#3b82f6",
    "validation_completed": "#10b981",
    "pr_created": "#8b5cf6",
    "workflow_failed": "#ef4444",
}


def build_slack_message(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build a Slack message block kit for the given event."""
    icon = EVENT_ICONS.get(event_type, "📋")
    color = EVENT_COLORS.get(event_type, "#6b7280")
    repo = data.get("repository", data.get("repo", "N/A"))
    inv_id = data.get("investigation_id")
    status = data.get("status", data.get("stage_status", ""))
    root_cause = data.get("root_cause", data.get("error_message", ""))
    fix_summary = data.get("fix_summary", data.get("summary", ""))
    pr_url = data.get("pr_url", "")
    confidence = data.get("confidence", data.get("confidence_score"))

    fields = [{"type": "mrkdwn", "text": f"*Repository:*\n{repo}"}]

    if inv_id:
        fields.append({"type": "mrkdwn", "text": f"*Investigation:*\n#{inv_id}"})

    if status:
        fields.append({"type": "mrkdwn", "text": f"*Status:*\n{status}"})

    if confidence:
        fields.append({"type": "mrkdwn", "text": f"*Confidence:*\n{confidence}"})

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{icon} {event_type.replace('_', ' ').title()}"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": fields,
        },
    ]

    if root_cause:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Root Cause:*\n{root_cause[:300]}"}})

    if fix_summary:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Fix Summary:*\n{fix_summary[:300]}"}})

    if pr_url:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"<{pr_url}|View Pull Request>"},
        })

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Self-Healing CI Agent · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"}],
    })

    return {
        "text": f"[Self-Healing CI] {event_type.replace('_', ' ').title()} — {repo}",
        "attachments": [{"color": color, "blocks": blocks}],
    }


async def send_slack_message(access_token: str, channel: str, message: dict[str, Any]) -> tuple[bool, str]:
    """Send a message to a Slack channel via the chat.postMessage API."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                f"{SLACK_API}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"channel": channel, **message},
            )
            result = resp.json()
            if result.get("ok"):
                return True, ""
            error = result.get("error", "unknown_error")
            logger.warning("Slack API error: %s", error)
            return False, error
        except Exception as e:
            logger.error("Failed to send Slack message: %s", str(e))
            return False, str(e)


async def list_slack_channels(access_token: str) -> tuple[bool, list[dict[str, str]] | str]:
    """List public channels available to the bot token."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{SLACK_API}/conversations.list",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"types": "public_channel", "limit": 200},
            )
            result = resp.json()
            if result.get("ok"):
                channels = [
                    {"id": c["id"], "name": c["name"]}
                    for c in result.get("channels", [])
                ]
                return True, channels
            error = result.get("error", "unknown_error")
            logger.warning("Slack conversations.list error: %s", error)
            return False, error
        except Exception as e:
            logger.error("Failed to list Slack channels: %s", str(e))
            return False, str(e)


async def exchange_oauth_code(code: str, redirect_uri: str) -> tuple[bool, dict[str, Any] | str]:
    """Exchange an OAuth authorization code for an access token."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                f"{SLACK_API}/oauth.v2.access",
                data={
                    "client_id": settings.slack_client_id or "",
                    "client_secret": settings.slack_client_secret or "",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            result = resp.json()
            if result.get("ok"):
                return True, {
                    "access_token": result["access_token"],
                    "workspace_id": result.get("team", {}).get("id", ""),
                    "workspace_name": result.get("team", {}).get("name", ""),
                }
            error = result.get("error", "unknown_error")
            logger.warning("Slack OAuth error: %s", error)
            return False, error
        except Exception as e:
            logger.error("Slack OAuth request failed: %s", str(e))
            return False, str(e)
