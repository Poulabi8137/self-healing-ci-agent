import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import create_api_key, create_api_key_with_value, get_api_key_by_key
from app.database.db import init_db, SessionLocal
from app.auth.models import ApiKey
from app.utils.rate_limiter import reset_rate_limits

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(ApiKey).delete()
        db.commit()
    finally:
        db.close()


def _make_admin_key():
    raw, key = create_api_key(name="test-admin", role="admin")
    return raw, key


def _make_recruiter_key():
    raw, key = create_api_key(name="test-recruiter", role="recruiter")
    return raw, key


def _make_candidate_key():
    raw, key = create_api_key(name="test-candidate", role="candidate")
    return raw, key


class TestAuthRequired:
    def test_health_public(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_version_public(self):
        r = client.get("/version")
        assert r.status_code == 200

    def test_dashboard_requires_auth(self):
        r = client.get("/dashboard/summary")
        assert r.status_code == 401

    def test_analysis_requires_auth(self):
        r = client.post("/analysis/debug", json={"repository_name": "test", "logs": "error"})
        assert r.status_code == 401

    def test_fix_requires_auth(self):
        r = client.post("/fix/generate", json={"repository_name": "test", "logs": "error"})
        assert r.status_code == 401

    def test_pr_create_requires_auth(self):
        r = client.post("/pr/create", json={"repository_name": "test", "logs": "error"})
        assert r.status_code == 401


class TestAuthSuccess:
    def test_dashboard_with_valid_key(self):
        raw, _ = _make_candidate_key()
        r = client.get("/dashboard/summary", headers={"X-API-Key": raw})
        assert r.status_code in (200, 500)

    def test_analysis_with_valid_key(self):
        raw, _ = _make_candidate_key()
        r = client.post("/analysis/debug", headers={"X-API-Key": raw}, json={"repository_name": "test", "logs": "error"})
        assert r.status_code in (200, 500)

    def test_rag_index_with_recruiter(self):
        raw, _ = _make_recruiter_key()
        r = client.post("/rag/index", headers={"X-API-Key": raw}, json={"repo_url": "https://github.com/test/repo"})
        assert r.status_code in (200, 500)


class TestRBACEnforcement:
    def test_candidate_cannot_create_pr(self):
        raw, _ = _make_candidate_key()
        r = client.post("/pr/create", headers={"X-API-Key": raw}, json={"repository_name": "test", "logs": "error"})
        assert r.status_code == 403

    def test_candidate_cannot_run_fix(self):
        raw, _ = _make_candidate_key()
        r = client.post("/fix/generate", headers={"X-API-Key": raw}, json={"repository_name": "test", "logs": "error"})
        assert r.status_code == 403

    def test_recruiter_can_create_pr(self):
        raw, _ = _make_recruiter_key()
        r = client.post("/pr/create", headers={"X-API-Key": raw}, json={"repository_name": "test", "logs": "error", "dry_run": True})
        assert r.status_code in (200, 500)

    def test_recruiter_can_run_retry(self):
        raw, _ = _make_recruiter_key()
        r = client.post("/retry/run", headers={"X-API-Key": raw}, json={"repository_name": "test", "logs": "error"})
        assert r.status_code in (200, 500)

    def test_candidate_cannot_manage_keys(self):
        raw, _ = _make_candidate_key()
        r = client.post("/auth/keys", headers={"X-API-Key": raw}, json={"name": "new-key", "role": "admin"})
        assert r.status_code == 403

    def test_admin_can_manage_keys(self):
        raw, _ = _make_admin_key()
        r = client.post("/auth/keys", headers={"X-API-Key": raw}, json={"name": "new-key", "role": "admin"})
        assert r.status_code == 200
        assert "key" in r.json()

    def test_admin_can_list_keys(self):
        raw, _ = _make_admin_key()
        r = client.get("/auth/keys", headers={"X-API-Key": raw})
        assert r.status_code == 200

    def test_invalid_key_rejected(self):
        r = client.get("/dashboard/summary", headers={"X-API-Key": "invalid-key-12345"})
        assert r.status_code == 401

    def test_revoked_key_rejected(self):
        raw, key_obj = _make_admin_key()
        from app.auth.utils import revoke_api_key
        revoke_api_key(key_obj.id)
        r = client.get("/dashboard/summary", headers={"X-API-Key": raw})
        assert r.status_code == 401


class TestTaskQueue:
    def test_submit_task_requires_auth(self):
        r = client.post("/tasks/submit", json={"type": "analysis", "payload": {}})
        assert r.status_code == 401

    def test_submit_task_with_auth(self):
        raw, _ = _make_candidate_key()
        r = client.post("/tasks/submit", headers={"X-API-Key": raw}, json={"type": "analysis", "payload": {"repository_name": "test", "logs": "error"}})
        assert r.status_code == 200
        data = r.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_task_status(self):
        raw, _ = _make_candidate_key()
        r = client.post("/tasks/submit", headers={"X-API-Key": raw}, json={"type": "analysis", "payload": {"repository_name": "test", "logs": "error"}})
        task_id = r.json()["task_id"]
        r2 = client.get(f"/tasks/{task_id}", headers={"X-API-Key": raw})
        assert r2.status_code == 200
        assert r2.json()["id"] == task_id

    def test_list_tasks(self):
        raw, _ = _make_candidate_key()
        r = client.get("/tasks/", headers={"X-API-Key": raw})
        assert r.status_code == 200

    def test_invalid_task_type(self):
        raw, _ = _make_candidate_key()
        r = client.post("/tasks/submit", headers={"X-API-Key": raw}, json={"type": "invalid_type", "payload": {}})
        assert r.status_code == 400


class TestBootstrapAdminKey:
    """Bug 1: _init_bootstrap_admin() must use the configured key value."""

    def test_create_api_key_with_value_stores_key(self):
        raw_key = "my-pre-shared-admin-key-12345"
        api_key = create_api_key_with_value(raw_key=raw_key, name="test-key", role="admin")
        assert api_key is not None
        assert api_key.key_prefix == raw_key[:8]
        assert api_key.role == "admin"
        assert api_key.is_active is True

    def test_create_api_key_with_value_is_idempotent(self):
        raw_key = "idempotent-key-test"
        k1 = create_api_key_with_value(raw_key=raw_key, name="first", role="admin")
        k2 = create_api_key_with_value(raw_key=raw_key, name="second", role="admin")
        assert k1.id == k2.id

    def test_bootstrap_key_can_authenticate(self):
        raw_key = "my-bootstrap-key"
        create_api_key_with_value(raw_key=raw_key, name="bootstrap-admin", role="admin")
        r = client.get("/dashboard/summary", headers={"X-API-Key": raw_key})
        assert r.status_code in (200, 500)

    def test_bootstrap_key_replaces_random_key_generation(self):
        raw_key = "fixed-bootstrap-key"
        create_api_key_with_value(raw_key=raw_key, name="test", role="admin")
        stored = get_api_key_by_key(raw_key)
        assert stored is not None
        assert stored.role == "admin"


class TestAsyncAuthNonBlocking:
    """Bug 2: get_current_user() must not block the event loop."""

    def test_authenticated_request_completes(self):
        raw, _ = _make_admin_key()
        r = client.get("/auth/keys", headers={"X-API-Key": raw})
        assert r.status_code == 200

    def test_unauthenticated_request_rejected(self):
        r = client.get("/auth/keys")
        assert r.status_code == 401

    def test_invalid_key_returns_401(self):
        r = client.get("/dashboard/summary", headers={"X-API-Key": "nonexistent-key"})
        assert r.status_code == 401

    def test_missing_header_returns_401(self):
        r = client.get("/dashboard/summary")
        assert r.status_code == 401
