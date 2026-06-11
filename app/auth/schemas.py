from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., max_length=128)
    role: str = Field(default="candidate", max_length=32)


class CreateApiKeyResponse(BaseModel):
    id: int
    key: str
    key_prefix: str
    name: str
    role: str
    message: str


class ApiKeyInfo(BaseModel):
    id: int
    key_prefix: str
    name: str
    role: str
    is_active: bool
    created_at: str
    last_used_at: str | None = None


class ListApiKeysResponse(BaseModel):
    api_keys: list[ApiKeyInfo]


class MeResponse(BaseModel):
    key_prefix: str
    name: str
    role: str
    created_at: str


class RevokeApiKeyResponse(BaseModel):
    message: str


# --- OAuth / JWT schemas ---


class OAuthLoginResponse(BaseModel):
    authorization_url: str


class UserInfoResponse(BaseModel):
    id: int
    email: str
    name: str | None = None
    avatar_url: str | None = None
    role: str
    created_at: str


class LogoutResponse(BaseModel):
    message: str
