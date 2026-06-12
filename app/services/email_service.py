"""Email notification service — HTML templates, plain text fallback, async delivery."""
import asyncio
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

EVENT_LABELS = {
    "investigation_started": "Investigation Started",
    "root_cause_identified": "Root Cause Identified",
    "fix_generated": "Fix Generated",
    "validation_completed": "Validation Completed",
    "pr_created": "Pull Request Created",
    "workflow_failed": "Workflow Failed",
}

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f6f8fa; margin: 0; padding: 24px;">
<table width="100%%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
<tr><td style="background: #2d3748; padding: 24px;">
<h1 style="color: #ffffff; margin: 0; font-size: 20px;">%(title)s</h1>
</td></tr>
<tr><td style="padding: 24px;">
%(body)s
</td></tr>
<tr><td style="background: #f6f8fa; padding: 16px 24px; font-size: 12px; color: #6a737d;">
<p style="margin: 0;">This notification was sent by the Self-Healing CI Agent.</p>
<p style="margin: 4px 0 0;">%(timestamp)s</p>
</td></tr>
</table>
</td></tr></table>
</body>
</html>"""

PLAINTEXT_TEMPLATE = """\
%(title)s
%(separator)s
%(body)s

—
This notification was sent by the Self-Healing CI Agent.
%(timestamp)s"""


def _build_event_data(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build context for notification templates from event data."""
    repo = data.get("repository", data.get("repo", "Unknown"))
    inv_id = data.get("investigation_id")
    status = data.get("status", data.get("stage_status", ""))
    root_cause = data.get("root_cause", data.get("error_message", ""))
    pr_url = data.get("pr_url", "")
    fix_summary = data.get("fix_summary", data.get("summary", ""))
    confidence = data.get("confidence", data.get("confidence_score"))

    ctx = {
        "repository": repo,
        "investigation_id": inv_id,
        "status": status,
        "root_cause": root_cause,
        "pr_url": pr_url,
        "fix_summary": fix_summary,
        "confidence": confidence,
    }
    return ctx


def _render_html_body(event_type: str, ctx: dict[str, Any]) -> str:
    parts = []
    parts.append(f'<p><strong>Repository:</strong> {ctx["repository"]}</p>')

    if ctx.get("investigation_id"):
        parts.append(f'<p><strong>Investigation ID:</strong> {ctx["investigation_id"]}</p>')

    if ctx.get("status"):
        parts.append(f'<p><strong>Status:</strong> {ctx["status"]}</p>')

    if ctx.get("root_cause"):
        parts.append(f'<p><strong>Root Cause:</strong> {ctx["root_cause"]}</p>')

    if ctx.get("fix_summary"):
        parts.append(f'<p><strong>Fix Summary:</strong> {ctx["fix_summary"]}</p>')

    if ctx.get("confidence"):
        parts.append(f'<p><strong>Confidence Score:</strong> {ctx["confidence"]}</p>')

    if ctx.get("pr_url"):
        parts.append(f'<p><a href="{ctx["pr_url"]}" style="display: inline-block; background: #2ea44f; color: #ffffff; padding: 8px 16px; border-radius: 6px; text-decoration: none;">View Pull Request</a></p>')

    return "\n".join(parts)


def _render_plaintext_body(event_type: str, ctx: dict[str, Any]) -> str:
    parts = []
    parts.append(f"Repository: {ctx['repository']}")

    if ctx.get("investigation_id"):
        parts.append(f"Investigation ID: {ctx['investigation_id']}")

    if ctx.get("status"):
        parts.append(f"Status: {ctx['status']}")

    if ctx.get("root_cause"):
        parts.append(f"Root Cause: {ctx['root_cause']}")

    if ctx.get("fix_summary"):
        parts.append(f"Fix Summary: {ctx['fix_summary']}")

    if ctx.get("confidence"):
        parts.append(f"Confidence Score: {ctx['confidence']}")

    if ctx.get("pr_url"):
        parts.append(f"Pull Request: {ctx['pr_url']}")

    return "\n".join(parts)


def build_email_content(event_type: str, data: dict[str, Any]) -> dict[str, str]:
    """Build subject, html_body, plaintext_body for a notification event."""
    label = EVENT_LABELS.get(event_type, event_type.replace("_", " ").title())
    ctx = _build_event_data(event_type, data)
    repo_name = ctx["repository"]
    subject = f"[Self-Healing CI] {label} — {repo_name}"

    html_body = HTML_TEMPLATE % {
        "title": label,
        "body": _render_html_body(event_type, ctx),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    plaintext_body = PLAINTEXT_TEMPLATE % {
        "title": label,
        "separator": "=" * len(label),
        "body": _render_plaintext_body(event_type, ctx),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    return {"subject": subject, "html": html_body, "text": plaintext_body}


async def send_email_async(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> tuple[bool, str]:
    """Send an email notification asynchronously.

    In production, this would use aiosmtplib, SendGrid, SES, etc.
    For MVP, logs the email and returns success to prove the pipeline.
    """
    try:
        logger.info(
            "EMAIL NOTIFICATION [to=%s] [subject=%s] [html_len=%d] [text_len=%d]",
            to_email, subject, len(html_body), len(text_body),
        )
        await asyncio.sleep(0.01)
        return True, ""
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False, str(e)
