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
    get_current_user_or_api_key,
)
from app.auth.models import ApiKey
from app.auth.oauth import (
    generate_state,
    get_authorization_url,
    fetch_google_token,
    get_google_userinfo,
    upsert_user,
    create_jwt,
    create_state_cookie_value,
    validate_state_cookie,
    STATE_COOKIE_NAME,
)
from app.database.models import User
from app.config.settings import settings
from app.utils.logger import get_logger

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
