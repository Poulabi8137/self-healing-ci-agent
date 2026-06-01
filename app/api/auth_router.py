from fastapi import APIRouter, HTTPException, Depends

from app.auth.schemas import CreateApiKeyRequest, CreateApiKeyResponse, ApiKeyInfo, ListApiKeysResponse, RevokeApiKeyResponse, MeResponse
from app.auth.utils import create_api_key, list_api_keys, revoke_api_key
from app.auth.dependencies import require_admin, get_current_user
from app.auth.models import ApiKey
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


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
