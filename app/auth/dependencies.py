import asyncio

from fastapi import Header, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader

from app.auth.utils import get_api_key_by_key
from app.auth.models import ApiKey
from app.auth.oauth import decode_jwt, get_user_by_id
from app.database.models import User

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(x_api_key: str = Depends(API_KEY_HEADER)) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    api_key = await asyncio.to_thread(get_api_key_by_key, x_api_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return api_key


async def optional_user(x_api_key: str | None = Header(default=None)) -> ApiKey | None:
    if not x_api_key:
        return None
    return await asyncio.to_thread(get_api_key_by_key, x_api_key)


async def get_current_jwt_user(request: Request) -> User:
    token = request.cookies.get("jwt")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=401, detail="Invalid or expired authentication token"
        )
    user = await asyncio.to_thread(get_user_by_id, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_user_or_api_key(
    request: Request,
    x_api_key: str = Depends(API_KEY_HEADER),
) -> User | ApiKey:
    """Try JWT cookie first, fall back to X-API-Key header."""
    token = request.cookies.get("jwt")
    if token:
        payload = decode_jwt(token)
        if payload:
            user = await asyncio.to_thread(get_user_by_id, int(payload["sub"]))
            if user:
                return user
    if x_api_key:
        api_key = await asyncio.to_thread(get_api_key_by_key, x_api_key)
        if api_key:
            return api_key
    raise HTTPException(status_code=401, detail="Not authenticated")


def require_role(*roles: str):
    async def role_checker(current_user: ApiKey = Depends(get_current_user)) -> ApiKey:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(roles)}")
        return current_user
    return role_checker


def require_jwt_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_jwt_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(roles)}")
        return current_user
    return role_checker


require_admin = require_role("admin")
require_recruiter = require_role("recruiter", "admin")
require_authenticated = get_current_user

require_admin_jwt = require_jwt_role("admin")
require_authenticated_jwt = get_current_jwt_user
