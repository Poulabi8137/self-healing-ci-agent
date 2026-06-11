from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.auth.schemas import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    ApiKeyInfo,
    ListApiKeysResponse,
    RevokeApiKeyResponse,
    MeResponse,
    OAuthLoginResponse,
    UserInfoResponse,
    LogoutResponse,
)
from app.auth.utils import create_api_key, list_api_keys, revoke_api_key
from app.auth.dependencies import (
    require_admin,
    get_current_user,
    get_current_jwt_user,
)
from app.auth.models import ApiKey
from app.auth.oauth import (
    generate_state,
    get_authorization_url as google_get_authorization_url,
    fetch_google_token,
    get_google_userinfo,
    upsert_user,
    create_jwt,
    create_state_cookie_value,
    validate_state_cookie,
    STATE_COOKIE_NAME,
)
from app.auth.github_oauth import (
    get_authorization_url as github_get_authorization_url,
    exchange_code as github_exchange_code,
    get_github_user_info_async,
    check_email_match,
)
from app.database.models import User
from app.config.settings import settings
from app.utils.logger import get_logger
from app.database.db import SessionLocal

logger = get_logger(__name__)

router = APIRouter()


# --- Existing API key endpoints (unchanged) ---


@router.get("/me", response_model=MeResponse)
async def api_auth_me(user: ApiKey = Depends(get_current_user)):
    return MeResponse(
        key_prefix=user.key_prefix,
        name=user.name,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.post("/keys", response_model=CreateApiKeyResponse)
async def api_create_api_key(req: CreateApiKeyRequest, admin=Depends(require_admin)):
    if req.role not in ("candidate", "recruiter", "admin"):
        raise HTTPException(status_code=400, detail="Role must be candidate, recruiter, or admin")
    raw, api_key = create_api_key(name=req.name, role=req.role)
    logger.info(f"Created API key '{req.name}' with role '{req.role}' (prefix={api_key.key_prefix})")
    return CreateApiKeyResponse(
        id=api_key.id,
        key=raw,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        role=api_key.role,
        message="Save this key — it will not be shown again",
    )


@router.get("/keys", response_model=ListApiKeysResponse)
async def api_list_api_keys(admin=Depends(require_admin)):
    keys = list_api_keys()
    return ListApiKeysResponse(
        api_keys=[
            ApiKeyInfo(
                id=k.id, key_prefix=k.key_prefix, name=k.name,
                role=k.role, is_active=k.is_active,
                created_at=k.created_at.isoformat() if k.created_at else "",
                last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            )
            for k in keys
        ]
    )


@router.delete("/keys/{key_id}", response_model=RevokeApiKeyResponse)
async def api_revoke_api_key(key_id: int, admin=Depends(require_admin)):
    if revoke_api_key(key_id):
        logger.info(f"Revoked API key id={key_id}")
        return RevokeApiKeyResponse(message=f"API key {key_id} revoked")
    raise HTTPException(status_code=404, detail="API key not found")


# --- OAuth / JWT endpoints ---


@router.get("/login")
async def oauth_login():
    """Initiate Google OAuth login. Redirects to Google's consent screen."""
    state = generate_state()
    authorization_url = get_authorization_url(state)
    signed_state = create_state_cookie_value(state)

    response = RedirectResponse(url=authorization_url, status_code=302)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=signed_state,
        max_age=600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/callback")
async def oauth_callback(request: Request, code: str | None = None, state: str | None = None):
    """Handle Google OAuth callback, issue JWT, redirect to app."""
    if not code:
        return JSONResponse(status_code=400, content={"detail": "Missing authorization code"})

    signed_state = request.cookies.get(STATE_COOKIE_NAME)
    if not signed_state or not validate_state_cookie(signed_state, state or ""):
        return JSONResponse(status_code=400, content={"detail": "Invalid state parameter"})

    try:
        token = fetch_google_token(code)
    except Exception as e:
        logger.error(f"Failed to fetch Google token: {e}")
        return JSONResponse(status_code=400, content={"detail": "Failed to exchange authorization code"})

    userinfo = get_google_userinfo(token)
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    if not google_id or not email:
        return JSONResponse(status_code=400, content={"detail": "Failed to get user info from Google"})

    user = upsert_user(
        google_id=google_id,
        email=email,
        name=userinfo.get("name"),
        avatar_url=userinfo.get("picture"),
    )

    jwt_token = create_jwt(user)

    logger.info(f"User authenticated: {email} (role={user.role})")

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="jwt",
        value=jwt_token,
        max_age=settings.jwt_ttl_seconds,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(key=STATE_COOKIE_NAME, path="/")
    return response


@router.post("/logout", response_model=LogoutResponse)
async def oauth_logout():
    """Clear JWT cookie to log out."""
    response = JSONResponse(content=LogoutResponse(message="Logged out").model_dump())
    response.delete_cookie(key="jwt", path="/")
    return response


@router.get("/user/me", response_model=UserInfoResponse)
async def oauth_user_me(
    user: User = Depends(get_current_jwt_user),
):
    """Return current user info from JWT session."""
    return UserInfoResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


# --- GitHub OAuth linking ---

GITHUB_STATE_COOKIE = "github_oauth_state"
GITHUB_LINK_PENDING_COOKIE = "github_link_pending"


@router.get("/github/login")
async def github_oauth_login(user: User = Depends(get_current_jwt_user)):
    """Initiate GitHub OAuth linking for the current user."""
    state = generate_state()
    authorization_url = github_get_authorization_url(state)
    signed_state = create_state_cookie_value(state)
    response = RedirectResponse(url=authorization_url, status_code=302)
    response.set_cookie(
        key=GITHUB_STATE_COOKIE,
        value=signed_state,
        max_age=600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/github/callback")
async def github_oauth_callback(
    request: Request,
    user: User = Depends(get_current_jwt_user),
    code: str | None = None,
    state: str | None = None,
):
    """Handle GitHub OAuth callback, compare emails, link account."""
    if not code:
        return RedirectResponse(url="/settings?github=error&reason=missing_code", status_code=302)

    signed_state = request.cookies.get(GITHUB_STATE_COOKIE)
    if not signed_state or not validate_state_cookie(signed_state, state or ""):
        return RedirectResponse(url="/settings?github=error&reason=invalid_state", status_code=302)

    try:
        token = github_exchange_code(code)
    except Exception as e:
        logger.error(f"GitHub OAuth token exchange failed: {e}")
        return RedirectResponse(url="/settings?github=error&reason=token_exchange", status_code=302)

    try:
        gh_info = await get_github_user_info_async(token)
    except Exception as e:
        logger.error(f"Failed to fetch GitHub user info: {e}")
        return RedirectResponse(url="/settings?github=error&reason=github_api", status_code=302)

    emails_match = check_email_match(user.email, gh_info)

    response = RedirectResponse(url="/settings", status_code=302)
    response.delete_cookie(key=GITHUB_STATE_COOKIE, path="/")

    if emails_match:
        _link_github_account(user.id, gh_info)
        logger.info(f"GitHub account linked: {user.email} -> {gh_info.github_username}")
        response = RedirectResponse(url="/settings?github=linked", status_code=302)
    else:
        pending = _create_pending_link_cookie(gh_info)
        response.set_cookie(
            key=GITHUB_LINK_PENDING_COOKIE,
            value=pending,
            max_age=600,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
        )
        response = RedirectResponse(url="/settings?github=email_mismatch", status_code=302)

    return response


@router.post("/github/link/confirm")
async def github_link_confirm(
    request: Request,
    user: User = Depends(get_current_jwt_user),
    accepted: bool = True,
):
    """Confirm or cancel GitHub account linking after email mismatch warning."""
    pending_data = request.cookies.get(GITHUB_LINK_PENDING_COOKIE)
    if not pending_data:
        raise HTTPException(status_code=400, detail="No pending GitHub link found")

    from app.auth.oauth import decode_jwt
    payload = decode_jwt(pending_data)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired pending link data")

    if not accepted:
        response = JSONResponse(content={"status": "cancelled", "message": "GitHub linking cancelled"})
        response.delete_cookie(key=GITHUB_LINK_PENDING_COOKIE, path="/")
        return response

    gh_info_data = payload.get("gh_info", {})
    from app.auth.github_oauth import GitHubUserInfo
    gh_info = GitHubUserInfo(
        github_id=gh_info_data["github_id"],
        github_username=gh_info_data["github_username"],
        github_email=gh_info_data.get("github_email"),
    )
    _link_github_account(user.id, gh_info)
    logger.info(f"GitHub account linked (mismatch override): {user.email} -> {gh_info.github_username}")

    response = JSONResponse(content={"status": "linked", "message": "GitHub account linked"})
    response.delete_cookie(key=GITHUB_LINK_PENDING_COOKIE, path="/")
    return response


@router.post("/github/unlink")
async def github_unlink(user: User = Depends(get_current_jwt_user)):
    """Unlink GitHub account from the current user."""
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            db_user.github_id = None
            db_user.github_username = None
            db_user.github_email = None
            db.commit()
        logger.info(f"GitHub account unlinked: {user.email}")
    finally:
        db.close()
    return {"status": "unlinked", "message": "GitHub account unlinked"}


def _link_github_account(user_id: int, gh_info) -> None:
    """Persist GitHub account info on the User record."""
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db_user.github_id = gh_info.github_id
            db_user.github_username = gh_info.github_username
            db_user.github_email = gh_info.github_email
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _create_pending_link_cookie(gh_info) -> str:
    """Sign pending GitHub link data for email mismatch confirmation flow."""
    from app.auth.oauth import create_state_cookie_value as sign
    import json
    payload_data = {
        "gh_info": {
            "github_id": gh_info.github_id,
            "github_username": gh_info.github_username,
            "github_email": gh_info.github_email,
        }
    }
    return sign(json.dumps(payload_data))
