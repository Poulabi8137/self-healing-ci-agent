import asyncio

from fastapi import Header, HTTPException, Depends
from fastapi.security import APIKeyHeader

from app.auth.utils import get_api_key_by_key
from app.auth.models import ApiKey

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


def require_role(*roles: str):
    async def role_checker(current_user: ApiKey = Depends(get_current_user)) -> ApiKey:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(roles)}")
        return current_user
    return role_checker


require_admin = require_role("admin")
require_recruiter = require_role("recruiter", "admin")
require_authenticated = get_current_user
