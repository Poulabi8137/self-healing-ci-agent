"""Tests for production hardening: rate limiting, exception leakage, body limits, JSON logging."""
import json
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.rate_limiter import reset_rate_limits
from app.database.db import init_db
from app.auth.utils import create_api_key_with_value
from app.database.db import SessionLocal
from app.auth.models import ApiKey

client = TestClient(app)

TEST_RAW_KEY = "hardening-test-key-001"


@pytest.fixture(autouse=True)
def setup():
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(ApiKey).delete()
        db.commit()
    finally:
        db.close()
    create_api_key_with_value(raw_key=TEST_RAW_KEY, name="harden-test", role="admin")


# ---------- Rate Limiting ----------

class TestRateLimiting:
    def test_rate_limit_auth_post_429(self):
        headers = {"X-API-Key": TEST_RAW_KEY}
        for _ in range(10):
            client.post("/auth/keys", json={"name": "x", "role": "candidate"}, headers=headers)
        r = client.post("/auth/keys", json={"name": "x", "role": "candidate"}, headers=headers)
        assert r.status_code == 429

    def test_retry_after_header_present(self):
        headers = {"X-API-Key": TEST_RAW_KEY}
        for _ in range(10):
            client.post("/auth/keys", json={"name": "x", "role": "candidate"}, headers=headers)
        r = client.post("/auth/keys", json={"name": "x", "role": "candidate"}, headers=headers)
        assert r.status_code == 429
        assert "Retry-After" in r.headers


# ---------- Exception Leakage ----------

class TestExceptionLeakage:
    def test_validation_error_no_traceback(self):
        """422 validation errors should never contain tracebacks."""
        r = client.post(
            "/fix/generate",
            json={"repository_name": "x" * 300, "logs": "bad"},
            headers={"X-API-Key": TEST_RAW_KEY}
        )
        assert r.status_code == 422
        detail_str = str(r.json())
        assert "Traceback" not in detail_str
        assert "File \"" not in detail_str

    def test_auth_error_no_traceback(self):
        """401 auth errors should not leak internals."""
        r = client.post(
            "/fix/generate",
            json={"repository_name": "repo", "logs": "bad"},
            headers={}
        )
        assert r.status_code == 401
        detail_str = str(r.json())
        assert "Traceback" not in detail_str
        assert "File \"" not in detail_str


# ---------- Request Body Limits ----------

class TestRequestBodyLimits:
    def test_repository_name_too_long(self):
        r = client.post(
            "/analysis/debug",
            json={"repository_name": "x" * 300, "logs": "error"},
            headers={"X-API-Key": TEST_RAW_KEY}
        )
        assert r.status_code == 422
        err = r.json()
        locs = [str(e.get("loc", [])) for e in err.get("detail", [])]
        assert any("repository_name" in loc for loc in locs)

    def test_auth_key_name_too_long(self):
        r = client.post(
            "/auth/keys",
            json={"name": "x" * 200, "role": "candidate"},
            headers={"X-API-Key": TEST_RAW_KEY}
        )
        assert r.status_code == 422

    def test_queue_type_too_long(self):
        r = client.post(
            "/tasks/submit",
            json={"type": "x" * 100, "payload": {}},
            headers={"X-API-Key": TEST_RAW_KEY}
        )
        assert r.status_code == 422


# ---------- Structured JSON Logging ----------

class TestJsonLogging:
    def test_json_sink_produces_valid_json(self, tmp_path):
        import json as _json
        from loguru import logger as _loguru
        _loguru.remove()
        json_file = tmp_path / "test.jsonl"

        def json_sink(msg):
            record = msg.record
            subset = {
                "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": record["level"].name,
                "module": record["name"],
                "message": record["message"],
            }
            extra = record.get("extra", {})
            if extra:
                subset.update({k: v for k, v in extra.items() if not k.startswith("_")})
            with open(json_file, "a", encoding="utf-8") as f:
                f.write(_json.dumps(subset) + "\n")

        _loguru.add(json_sink)
        _loguru.bind(request_id="req-001").info("hello")
        _loguru.remove()
        raw = json_file.read_bytes().decode("utf-8").strip()
        lines = raw.splitlines()
        assert len(lines) == 1
        record = _json.loads(lines[0])
        assert record["message"] == "hello"
        assert record["request_id"] == "req-001"

    def test_loguru_serialize_includes_extra(self, tmp_path):
        import json as _json
        from loguru import logger as _loguru
        _loguru.remove()
        json_file = tmp_path / "test_req.jsonl"
        _loguru.add(json_file, serialize=True)
        _loguru.bind(request_id="abc-123").info("req test")
        _loguru.remove()
        raw = json_file.read_bytes().decode("utf-8").strip()
        assert "abc-123" in raw
