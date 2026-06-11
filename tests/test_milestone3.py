"""
Milestone 3 validation: webhook verification, replay protection,
failure detection, investigation triggering, event persistence.

Tests use mocked data — no real GitHub API calls.
"""
import json
import hmac
import hashlib
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import settings
from app.database.db import SessionLocal, init_db
from app.database.models import (
    User, Repository, GitHubInstallation, Failure,
    Investigation, WebhookEvent, InvestigationEvent,
)
from app.services.webhook_handler import verify_signature, process_webhook
from app.utils.rate_limiter import reset_rate_limits

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup():
    saved = settings.github_app_webhook_secret
    settings.github_app_webhook_secret = "test-webhook-secret"
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(InvestigationEvent).delete()
        db.query(Investigation).delete()
        db.query(Failure).delete()
        db.query(WebhookEvent).delete()
        db.query(Repository).delete()
        db.query(GitHubInstallation).delete()
        db.query(User).delete()
        db.commit()
        yield
    finally:
        settings.github_app_webhook_secret = saved
        db.close()


def _create_repo(full_name: str = "test-org/test-repo",
                  installation_id: int = 1,
                  is_active: bool = True) -> Repository:
    db = SessionLocal()
    try:
        repo = Repository(
            name=full_name.split("/")[1],
            full_name=full_name,
            github_installation_id=installation_id,
            is_active=is_active,
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        return repo
    finally:
        db.close()


def _sign_payload(body: bytes) -> str:
    return "sha256=" + hmac.new(
        settings.github_app_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()


WORKFLOW_FAILURE_PAYLOAD = {
    "action": "completed",
    "workflow_run": {
        "id": 12345678,
        "name": "CI",
        "conclusion": "failure",
        "status": "completed",
        "head_branch": "main",
    },
    "repository": {
        "full_name": "test-org/test-repo",
        "name": "test-repo",
    },
    "sender": {"login": "test-user"},
}

INSTALLATION_CREATED_PAYLOAD = {
    "action": "created",
    "installation": {
        "id": 100,
        "account": {
            "login": "test-org",
            "type": "Organization",
            "avatar_url": "https://avatars.example.com/1",
            "html_url": "https://github.com/test-org",
        },
    },
    "sender": {"id": 500, "login": "admin"},
}


class TestSignatureVerification:
    def test_valid_signature_passes(self):
        body = json.dumps({"test": "data"}).encode()
        sig = _sign_payload(body)
        assert verify_signature(body, sig) is True

    def test_invalid_signature_fails(self):
        body = json.dumps({"test": "data"}).encode()
        assert verify_signature(body, "sha256=invalid") is False

    def test_missing_signature_fails(self):
        body = json.dumps({"test": "data"}).encode()
        assert verify_signature(body, None) is False

    def test_wrong_key_fails(self):
        body = json.dumps({"test": "data"}).encode()
        wrong_sig = "sha256=" + hmac.new(
            b"wrong-secret", body, hashlib.sha256
        ).hexdigest()
        assert verify_signature(body, wrong_sig) is False


class TestWebhookEndpoint:
    def test_missing_headers_returns_400(self):
        r = client.post("/webhooks/github", content=b"{}", headers={"Content-Type": "application/json"})
        assert r.status_code == 400

    def test_invalid_signature_returns_401(self):
        body = json.dumps(WORKFLOW_FAILURE_PAYLOAD).encode()
        r = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": "delivery-001",
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json",
            },
        )
        assert r.status_code == 401

    def _send_webhook(self, payload: dict, delivery_id: str) -> tuple[bytes, str]:
        body = json.dumps(payload).encode()
        sig = _sign_payload(body)
        r = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": delivery_id,
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json",
            },
        )
        return r, body

    def test_valid_workflow_failure_creates_investigation(self):
        _create_repo()
        r, _ = self._send_webhook(WORKFLOW_FAILURE_PAYLOAD, "delivery-002")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "investigation_created"
        assert "investigation_id" in data
        assert "failure_id" in data

        # Verify DB records
        db = SessionLocal()
        try:
            failure = db.query(Failure).filter(Failure.id == data["failure_id"]).first()
            assert failure is not None
            assert failure.status == "detected"
            assert failure.run_id == "12345678"

            investigation = db.query(Investigation).filter(
                Investigation.id == data["investigation_id"]
            ).first()
            assert investigation is not None
            assert investigation.status == "detecting"

            events = db.query(InvestigationEvent).filter(
                InvestigationEvent.investigation_id == investigation.id
            ).all()
            assert len(events) >= 1
            assert events[0].event_type == "failure_detected"
        finally:
            db.close()


class TestReplayProtection:
    def test_duplicate_delivery_returns_200_and_skips(self):
        _create_repo()
        body = json.dumps(WORKFLOW_FAILURE_PAYLOAD).encode()
        sig = _sign_payload(body)
        headers = {
            "X-GitHub-Event": "workflow_run",
            "X-GitHub-Delivery": "delivery-replay-001",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        }

        r1 = client.post("/webhooks/github", content=body, headers=headers)
        assert r1.status_code == 200
        assert r1.json()["status"] == "investigation_created"

        r2 = client.post("/webhooks/github", content=body, headers=headers)
        assert r2.status_code == 200
        assert r2.json()["status"] == "skipped"
        assert r2.json()["reason"] == "duplicate"

    def test_unique_deliveries_both_process(self):
        _create_repo()
        for i, run_id in enumerate([11111, 22222]):
            payload = {
                "action": "completed",
                "workflow_run": {
                    "id": run_id, "name": "CI",
                    "conclusion": "failure", "status": "completed",
                    "head_branch": "main",
                },
                "repository": {"full_name": "test-org/test-repo", "name": "test-repo"},
                "sender": {"login": "test-user"},
            }
            body = json.dumps(payload).encode()
            sig = _sign_payload(body)
            r = client.post(
                "/webhooks/github",
                content=body,
                headers={
                    "X-GitHub-Event": "workflow_run",
                    "X-GitHub-Delivery": f"delivery-unique-{i}",
                    "X-Hub-Signature-256": sig,
                    "Content-Type": "application/json",
                },
            )
            assert r.status_code == 200
            assert r.json()["status"] == "investigation_created"


class TestInvestigationEventPersistence:
    def test_failure_detected_event_stored(self):
        _create_repo()
        body = json.dumps(WORKFLOW_FAILURE_PAYLOAD).encode()
        sig = _sign_payload(body)
        r = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": "delivery-events-001",
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json",
            },
        )
        inv_id = r.json()["investigation_id"]

        db = SessionLocal()
        try:
            events = db.query(InvestigationEvent).filter(
                InvestigationEvent.investigation_id == inv_id
            ).order_by(InvestigationEvent.created_at).all()
            assert len(events) >= 1
            evt = events[0]
            assert evt.event_type == "failure_detected"
            data = json.loads(evt.data)
            assert data["repository"] == "test-org/test-repo"
            assert data["run_id"] == 12345678
        finally:
            db.close()


class TestInactiveRepository:
    def test_inactive_repo_ignores_failure(self):
        _create_repo(is_active=False)
        body = json.dumps(WORKFLOW_FAILURE_PAYLOAD).encode()
        sig = _sign_payload(body)
        r = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": "delivery-inactive-001",
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "ignored"
        assert r.json()["reason"] == "repository not active"


class TestNonFailureEvent:
    def test_successful_workflow_ignored(self):
        success_payload = dict(WORKFLOW_FAILURE_PAYLOAD)
        success_payload["workflow_run"] = dict(success_payload["workflow_run"])
        success_payload["workflow_run"]["conclusion"] = "success"

        body = json.dumps(success_payload).encode()
        sig = _sign_payload(body)
        r = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": "delivery-success-001",
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "ignored"
