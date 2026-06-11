"""
Milestone 2 validation: JWT auth, admin role, API keys, logout, state.

Runs against the actual FastAPI app via TestClient.
JWTs are generated directly (no Google OAuth call needed for validation).
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt
from app.main import app
from app.config.settings import settings
from app.auth.oauth import create_jwt, generate_state, create_state_cookie_value, validate_state_cookie
from app.auth.utils import create_api_key
from app.database.db import SessionLocal, init_db
from app.database.models import User
from app.utils.rate_limiter import reset_rate_limits

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup():
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()
        yield
    finally:
        db.close()


def _create_test_user(email: str = "test@example.com", name: str = "Test User",
                       role: str = "user") -> User:
    db = SessionLocal()
    try:
        user = User(
            google_id=f"google_{email}",
            email=email,
            name=name,
            role=role,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


class TestJWTNoCookie:
    def test_user_me_returns_401_without_cookie(self):
        r = client.get("/auth/user/me")
        assert r.status_code == 401


class TestJWTExpired:
    def test_user_me_returns_401_with_expired_jwt(self):
        user = _create_test_user()
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "iat": past - timedelta(seconds=10),
            "exp": past,
        }
        expired_token = jose_jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
        r = client.get("/auth/user/me", cookies={"jwt": expired_token})
        assert r.status_code == 401


class TestJWTValid:
    def test_user_me_returns_user_info(self):
        user = _create_test_user()
        token = create_jwt(user)
        r = client.get("/auth/user/me", cookies={"jwt": token})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == user.email
        assert data["name"] == user.name
        assert data["role"] == user.role
        assert data["id"] == user.id

    def test_user_me_has_correct_fields(self):
        user = _create_test_user(email="alice@example.com", name="Alice")
        token = create_jwt(user)
        r = client.get("/auth/user/me", cookies={"jwt": token})
        data = r.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "role" in data
        assert "avatar_url" in data
        assert "created_at" in data


class TestAdminRole:
    def test_admin_email_gets_admin_role(self):
        original = settings.admin_email
        settings.admin_email = "admin@example.com"
        try:
            from app.auth.oauth import upsert_user
            user = upsert_user(
                google_id="google_admin",
                email="admin@example.com",
                name="Admin",
                avatar_url=None,
            )
            assert user.role == "admin"
        finally:
            settings.admin_email = original

    def test_non_admin_email_gets_user_role(self):
        original = settings.admin_email
        settings.admin_email = "someone-else@example.com"
        try:
            from app.auth.oauth import upsert_user
            user = upsert_user(
                google_id="google_user",
                email="user@example.com",
                name="User",
                avatar_url=None,
            )
            assert user.role == "user"
        finally:
            settings.admin_email = original


class TestNonAdminUser:
    def test_non_admin_user_me_returns_user_role(self):
        user = _create_test_user(email="regular@example.com", role="user")
        token = create_jwt(user)
        r = client.get("/auth/user/me", cookies={"jwt": token})
        assert r.status_code == 200
        assert r.json()["role"] == "user"


class TestAPIKeyStillWorks:
    def test_me_with_api_key(self):
        raw, _ = create_api_key(name="test-key", role="candidate")
        r = client.get("/auth/me", headers={"X-API-Key": raw})
        assert r.status_code == 200
        data = r.json()
        assert data["key_prefix"] == raw[:8]
        assert data["role"] == "candidate"

    def test_dashboard_with_api_key(self):
        raw, _ = create_api_key(name="test-key-2", role="admin")
        r = client.get("/dashboard/summary", headers={"X-API-Key": raw})
        assert r.status_code in (200, 500)

    def test_invalid_api_key_rejected(self):
        r = client.get("/auth/me", headers={"X-API-Key": "invalid-key"})
        assert r.status_code == 401


class TestLogout:
    def test_logout_clears_cookie(self):
        user = _create_test_user()
        token = create_jwt(user)
        r = client.post("/auth/logout", cookies={"jwt": token})
        assert r.status_code == 200
        # Verify cookie is cleared (Set-Cookie with max-age=0)
        set_cookie = r.headers.get("set-cookie", "")
        assert "jwt=" in set_cookie
        assert "Max-Age=0" in set_cookie

    def test_logout_response_has_set_cookie_header(self):
        user = _create_test_user()
        token = create_jwt(user)
        r = client.post("/auth/logout", cookies={"jwt": token})
        assert r.status_code == 200
        assert "jwt=" in r.headers.get("set-cookie", "")


class TestOAuthStateValidation:
    def test_valid_state_passes(self):
        state = generate_state()
        signed = create_state_cookie_value(state)
        assert validate_state_cookie(signed, state) is True

    def test_invalid_state_fails(self):
        state = generate_state()
        signed = create_state_cookie_value(state)
        assert validate_state_cookie(signed, "wrong-state") is False

    def test_tampered_cookie_fails(self):
        state = generate_state()
        signed = create_state_cookie_value(state)
        tampered = signed[:-5] + "XXXXX"
        assert validate_state_cookie(tampered, state) is False

    def test_expired_state_fails(self):
        state = generate_state()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            "state": state,
            "exp": past,
            "iat": past - timedelta(seconds=10),
        }
        expired_signed = jose_jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
        assert validate_state_cookie(expired_signed, state) is False
