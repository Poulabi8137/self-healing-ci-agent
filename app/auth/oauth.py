import secrets
from datetime import datetime, timezone, timedelta

from authlib.integrations.requests_client import OAuth2Session
from jose import jwt as jose_jwt, JWTError

from app.config.settings import settings
from app.database.db import SessionLocal
from app.database.models import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
STATE_TTL_SECONDS = 600  # 10 minutes


def _get_redirect_uri() -> str:
    return f"{settings.oauth_callback_url}/auth/callback"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def create_oauth_session(state: str | None = None) -> OAuth2Session:
    return OAuth2Session(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scope="openid email profile",
        redirect_uri=_get_redirect_uri(),
        state=state,
    )


def get_authorization_url(state: str) -> str:
    session = create_oauth_session(state=state)
    uri, _ = session.create_authorization_url(GOOGLE_AUTH_URL)
    return uri


def fetch_google_token(code: str) -> dict:
    session = create_oauth_session()
    return session.fetch_token(GOOGLE_TOKEN_URL, code=code)


def get_google_userinfo(token: dict) -> dict:
    """Extract user info from Google id_token or userinfo endpoint."""
    id_token = token.get("id_token")
    if id_token:
        try:
            claims = jose_jwt.get_unverified_claims(id_token)
            if claims.get("aud") != settings.google_client_id:
                logger.warning("Google id_token aud mismatch")
            return claims
        except Exception as e:
            logger.warning(f"Failed to decode id_token: {e}")

    session = create_oauth_session()
    session.token = token
    resp = session.get(GOOGLE_USERINFO_URL)
    resp.raise_for_status()
    return resp.json()


def upsert_user(google_id: str, email: str, name: str | None, avatar_url: str | None) -> User:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            user.name = name or user.name
            user.avatar_url = avatar_url or user.avatar_url
            user.last_login_at = datetime.now(timezone.utc)
        else:
            role = "admin" if email == settings.admin_email else "user"
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
                role=role,
                last_login_at=datetime.now(timezone.utc),
            )
            db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_jwt(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_ttl_seconds),
    }
    return jose_jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> dict | None:
    try:
        return jose_jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None


def get_user_by_id(user_id: int) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


STATE_COOKIE_NAME = "oauth_state"


def create_state_cookie_value(state: str) -> str:
    """Sign the state value with a short-lived JWT for secure cookie storage."""
    now = datetime.now(timezone.utc)
    payload = {
        "state": state,
        "exp": now + timedelta(seconds=STATE_TTL_SECONDS),
        "iat": now,
    }
    return jose_jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def validate_state_cookie(cookie_value: str, returned_state: str) -> bool:
    """Validate returned state against signed cookie value."""
    try:
        payload = jose_jwt.decode(
            cookie_value, settings.jwt_secret, algorithms=["HS256"]
        )
        return payload.get("state") == returned_state
    except JWTError:
        return False
