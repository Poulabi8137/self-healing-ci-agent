"""Tests for Phase 9 — Notifications (email, Slack, persistence, API, auth)."""
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database.db import SessionLocal, init_db
from app.database.models import (
    Notification,
    NotificationSetting,
    SlackWorkspace,
    User,
)
from app.main import app
from app.services.email_service import build_email_content, send_email_async
from app.services.slack_service import build_slack_message, send_slack_message, list_slack_channels
from app.services.notification_dispatcher import (
    NOTIFIABLE_EVENTS,
    process_event,
    _get_recipient_users,
    _get_user_email,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    db = SessionLocal()
    try:
        db.query(Notification).delete()
        db.query(NotificationSetting).delete()
        db.query(SlackWorkspace).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


def _make_user(email="notif-test@example.com", role="member"):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(email=email, role=role)
            db.add(u)
            db.commit()
            db.refresh(u)
        return u
    finally:
        db.close()


def _make_admin():
    return _make_user(email="admin-notif@example.com", role="admin")


def _login(user):
    from app.auth.oauth import create_jwt
    jwt = create_jwt(user)
    return {"Cookie": f"jwt={jwt}"}


# ---------------------------------------------------------------------------
# 1. Notification Persistence Tests
# ---------------------------------------------------------------------------

class TestNotificationPersistence:
    def test_create_notification(self):
        u = _make_user()
        db = SessionLocal()
        try:
            n = Notification(
                user_id=u.id,
                channel_type="email",
                event_type="investigation_started",
                status="sent",
                recipient="test@example.com",
                subject="Test Subject",
                delivered_at=datetime.now(timezone.utc),
            )
            db.add(n)
            db.commit()
            db.refresh(n)
            assert n.id
            assert n.user_id == u.id
            assert n.channel_type == "email"
            assert n.event_type == "investigation_started"
            assert n.status == "sent"
        finally:
            db.close()

    def test_notification_defaults(self):
        u = _make_user()
        db = SessionLocal()
        try:
            n = Notification(user_id=u.id, channel_type="email", event_type="fix_generated")
            db.add(n)
            db.commit()
            db.refresh(n)
            assert n.status == "pending"
            assert n.delivered_at is None
            assert n.failure_reason is None
        finally:
            db.close()

    def test_failed_notification(self):
        u = _make_user()
        db = SessionLocal()
        try:
            n = Notification(
                user_id=u.id,
                channel_type="slack",
                event_type="workflow_failed",
                status="failed",
                failure_reason="channel_not_found",
            )
            db.add(n)
            db.commit()
            db.refresh(n)
            assert n.status == "failed"
            assert n.failure_reason == "channel_not_found"
        finally:
            db.close()


class TestNotificationSettingPersistence:
    def test_create_settings(self):
        u = _make_user()
        db = SessionLocal()
        try:
            s = NotificationSetting(user_id=u.id)
            db.add(s)
            db.commit()
            db.refresh(s)
            assert s.email_enabled is True
            assert s.slack_enabled is False
        finally:
            db.close()

    def test_update_settings(self):
        u = _make_user()
        db = SessionLocal()
        try:
            s = NotificationSetting(user_id=u.id, email_enabled=False, slack_enabled=True)
            db.add(s)
            db.commit()
            db.refresh(s)
            assert s.email_enabled is False
            assert s.slack_enabled is True
        finally:
            db.close()


class TestSlackWorkspacePersistence:
    def test_create_workspace(self):
        u = _make_user()
        db = SessionLocal()
        try:
            w = SlackWorkspace(
                user_id=u.id,
                workspace_id="T12345",
                workspace_name="Test Workspace",
                access_token="xoxb-test-token",
                selected_channel_id="C12345",
                selected_channel_name="general",
            )
            db.add(w)
            db.commit()
            db.refresh(w)
            assert w.workspace_id == "T12345"
            assert w.access_token == "xoxb-test-token"
            assert w.selected_channel_name == "general"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 2. Email Service Tests
# ---------------------------------------------------------------------------

class TestEmailService:
    def test_build_email_content_investigation_started(self):
        result = build_email_content("investigation_started", {
            "repository": "test/repo",
            "investigation_id": 1,
        })
        assert "[Self-Healing CI]" in result["subject"]
        assert "Investigation Started" in result["subject"]
        assert "test/repo" in result["subject"]
        assert "test/repo" in result["html"]
        assert "test/repo" in result["text"]
        assert "Investigation ID" in result["html"]
        assert "1" in result["text"]

    def test_build_email_content_pr_created(self):
        result = build_email_content("pr_created", {
            "repository": "test/repo",
            "investigation_id": 42,
            "pr_url": "https://github.com/test/repo/pull/1",
        })
        assert "Pull Request Created" in result["subject"]
        assert "https://github.com/test/repo/pull/1" in result["html"]
        assert "View Pull Request" in result["html"]

    def test_build_email_content_workflow_failed(self):
        result = build_email_content("workflow_failed", {
            "repository": "test/repo",
            "error_message": "SyntaxError: invalid syntax",
        })
        assert "Workflow Failed" in result["subject"]
        assert "SyntaxError" in result["html"]
        assert "SyntaxError" in result["text"]

    def test_build_email_content_unknown_event(self):
        result = build_email_content("some_custom_event", {
            "repository": "test/repo",
        })
        assert "Some Custom Event" in result["subject"] or "some_custom_event" in result["subject"]

    @pytest.mark.asyncio
    async def test_send_email_async_success(self):
        success, error = await send_email_async(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
            text_body="Test",
        )
        assert success is True
        assert error == ""

    @pytest.mark.asyncio
    async def test_send_email_async_produces_content(self):
        """Verify the email content generation produces valid output."""
        content = build_email_content("investigation_started", {
            "repository": "my-org/my-repo",
            "investigation_id": 7,
        })
        assert len(content["subject"]) > 0
        assert len(content["html"]) > 0
        assert len(content["text"]) > 0
        assert content["html"].startswith("<!DOCTYPE html>")
        assert "my-org/my-repo" in content["text"]


# ---------------------------------------------------------------------------
# 3. Slack Integration Tests
# ---------------------------------------------------------------------------

class TestSlackService:
    def test_build_slack_message_investigation_started(self):
        msg = build_slack_message("investigation_started", {
            "repository": "test/repo",
            "investigation_id": 1,
        })
        assert "investigation_started" in msg["text"] or "Investigation Started" in msg["text"] or "🔍" in str(msg)
        assert len(msg["attachments"]) == 1

    def test_build_slack_message_pr_created(self):
        msg = build_slack_message("pr_created", {
            "repository": "test/repo",
            "investigation_id": 42,
            "pr_url": "https://github.com/test/repo/pull/1",
        })
        assert "Pull Request" in str(msg)
        assert "https://github.com/test/repo/pull/1" in str(msg)

    def test_build_slack_message_workflow_failed(self):
        msg = build_slack_message("workflow_failed", {
            "repository": "test/repo",
            "error_message": "Build failed",
        })
        assert "Workflow Failed" in msg["text"] or "❌" in str(msg)
        assert "Build failed" in str(msg)

    @pytest.mark.asyncio
    async def test_send_slack_message_network_error(self):
        """Test that send_slack_message handles network errors gracefully."""
        with patch("app.services.slack_service.httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            success, error = await send_slack_message(
                access_token="xoxb-test",
                channel="C12345",
                message={"text": "Test"},
            )
            assert success is False
            assert "Connection refused" in error

    @pytest.mark.asyncio
    async def test_list_slack_channels_network_error(self):
        """Test that list_slack_channels handles network errors gracefully."""
        with patch("app.services.slack_service.httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Timeout")

            success, result = await list_slack_channels("xoxb-test")
            assert success is False
            assert "Timeout" in str(result)


from app.services.slack_service import exchange_oauth_code, list_slack_channels


# ---------------------------------------------------------------------------
# 4. Notification Dispatcher Tests
# ---------------------------------------------------------------------------

class TestNotificationDispatcher:
    def test_notifiable_events_set(self):
        expected = {
            "investigation_started",
            "root_cause_identified",
            "fix_generated",
            "validation_completed",
            "pr_created",
            "workflow_failed",
        }
        assert NOTIFIABLE_EVENTS == expected

    def test_get_recipient_users_admin(self):
        admin = _make_admin()
        u = _make_user()
        db = SessionLocal()
        try:
            users = _get_recipient_users(db, "investigation_started", {})
            user_ids = [u.id for u in users]
            assert admin.id in user_ids
        finally:
            db.close()

    def test_get_user_email(self):
        u = _make_user(email="test@example.com")
        assert _get_user_email(u) == "test@example.com"

    def test_get_user_email_fallback(self):
        db = SessionLocal()
        try:
            u = User(email="fallback@test.com", github_email="gh@example.com")
            db.add(u)
            db.commit()
            assert _get_user_email(u) == "fallback@test.com"
        finally:
            db.close()

    def test_get_user_email_none(self):
        db = SessionLocal()
        try:
            u = User(email="noemail@test.com", github_email=None)
            db.add(u)
            db.commit()
            assert _get_user_email(u) == "noemail@test.com"
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_process_event_ignores_non_notifiable(self):
        """Events not in NOTIFIABLE_EVENTS should be silently ignored."""
        # Should not raise
        await process_event("logs_collected", {"repository": "test/repo"})

    @pytest.mark.asyncio
    async def test_process_event_without_settings(self):
        """Event should be processed even without existing settings."""
        u = _make_user()
        db = SessionLocal()
        try:
            # Ensure no settings exist
            db.query(NotificationSetting).filter(NotificationSetting.user_id == u.id).delete()
            db.commit()
        finally:
            db.close()

        await process_event("investigation_started", {"repository": "test/repo", "investigation_id": 1})


# ---------------------------------------------------------------------------
# 5. API Tests
# ---------------------------------------------------------------------------

class TestNotificationsAPI:
    def test_get_notifications_requires_auth(self):
        resp = client.get("/api/notifications")
        assert resp.status_code == 401

    def test_get_notifications_empty(self):
        u = _make_user()
        resp = client.get("/api/notifications", headers=_login(u))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["notifications"] == []

    def test_get_notifications_with_data(self):
        u = _make_user()
        db = SessionLocal()
        try:
            for i in range(3):
                db.add(Notification(
                    user_id=u.id, channel_type="email",
                    event_type="investigation_started", status="sent",
                ))
            db.commit()
        finally:
            db.close()

        resp = client.get("/api/notifications", headers=_login(u))
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_get_notifications_scoped_to_user(self):
        u1 = _make_user(email="u1@example.com")
        u2 = _make_user(email="u2@example.com")
        db = SessionLocal()
        try:
            db.add(Notification(user_id=u1.id, channel_type="email", event_type="fix_generated"))
            db.add(Notification(user_id=u2.id, channel_type="slack", event_type="pr_created"))
            db.commit()
        finally:
            db.close()

        resp = client.get("/api/notifications", headers=_login(u1))
        assert resp.json()["total"] == 1

    def test_get_settings_creates_defaults(self):
        u = _make_user()
        resp = client.get("/api/notifications/settings", headers=_login(u))
        assert resp.status_code == 200
        assert resp.json()["email_enabled"] is True
        assert resp.json()["slack_enabled"] is False

    def test_update_settings(self):
        u = _make_user()
        resp = client.put(
            "/api/notifications/settings",
            json={"email_enabled": False, "slack_enabled": True},
            headers=_login(u),
        )
        assert resp.status_code == 200
        assert resp.json()["email_enabled"] is False
        assert resp.json()["slack_enabled"] is True

        # Verify persistence
        resp2 = client.get("/api/notifications/settings", headers=_login(u))
        assert resp2.json()["email_enabled"] is False
        assert resp2.json()["slack_enabled"] is True

    def test_update_settings_partial(self):
        u = _make_user()
        resp = client.put(
            "/api/notifications/settings",
            json={"email_enabled": False},
            headers=_login(u),
        )
        assert resp.status_code == 200
        assert resp.json()["email_enabled"] is False

        resp2 = client.get("/api/notifications/settings", headers=_login(u))
        assert resp2.json()["email_enabled"] is False
        assert resp2.json()["slack_enabled"] is False


class TestSlackAPI:
    def test_slack_status_not_connected(self):
        u = _make_user()
        resp = client.get("/api/slack/status", headers=_login(u))
        assert resp.status_code == 200
        assert resp.json()["connected"] is False

    def test_slack_channels_requires_connection(self):
        u = _make_user()
        resp = client.get("/api/slack/channels", headers=_login(u))
        assert resp.status_code == 404
        assert "No Slack workspace" in resp.json()["detail"]

    def test_disconnect_without_connection(self):
        u = _make_user()
        resp = client.post("/api/slack/disconnect", headers=_login(u))
        assert resp.status_code == 404

    def test_slack_connect_no_code(self):
        """Connect with empty code should fail."""
        u = _make_user()
        resp = client.post(
            "/api/slack/connect",
            json={"code": "", "redirect_uri": "http://localhost:5173/settings"},
            headers=_login(u),
        )
        assert resp.status_code == 400

    def test_select_channel_without_connection(self):
        u = _make_user()
        resp = client.put(
            "/api/slack/channel",
            json={"channel_id": "C123", "channel_name": "general"},
            headers=_login(u),
        )
        assert resp.status_code == 404

    def test_slack_api_auth_required(self):
        resp = client.get("/api/slack/status")
        assert resp.status_code == 401
        resp = client.get("/api/slack/channels")
        assert resp.status_code == 401
        resp = client.post("/api/slack/connect", json={"code": "x", "redirect_uri": "x"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 6. Authorization Tests
# ---------------------------------------------------------------------------

class TestAuthorization:
    def test_other_user_cannot_see_notifications(self):
        u1 = _make_user(email="u1-auth@example.com")
        u2 = _make_user(email="u2-auth@example.com")

        db = SessionLocal()
        try:
            db.add(Notification(user_id=u1.id, channel_type="email", event_type="fix_generated"))
            db.commit()
        finally:
            db.close()

        resp = client.get("/api/notifications", headers=_login(u2))
        assert resp.json()["total"] == 0

    def test_notification_pagination(self):
        u = _make_user()
        db = SessionLocal()
        try:
            for i in range(5):
                db.add(Notification(
                    user_id=u.id, channel_type="email",
                    event_type="investigation_started", status="sent",
                ))
            db.commit()
        finally:
            db.close()

        resp = client.get("/api/notifications?limit=2", headers=_login(u))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["notifications"]) == 2
        assert data["limit"] == 2
