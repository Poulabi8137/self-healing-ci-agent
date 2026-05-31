import hashlib
import secrets

from app.auth.models import ApiKey
from app.database.db import SessionLocal


def generate_api_key() -> tuple[str, str, str]:
    raw = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    key_prefix = raw[:8]
    return raw, key_hash, key_prefix


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def get_api_key_by_key(raw_key: str) -> ApiKey | None:
    key_hash = hash_key(raw_key)
    db = SessionLocal()
    try:
        return db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True)).first()
    finally:
        db.close()


def create_api_key(name: str, role: str = "candidate") -> tuple[str, ApiKey]:
    raw, key_hash, key_prefix = generate_api_key()
    db = SessionLocal()
    try:
        api_key = ApiKey(key_prefix=key_prefix, key_hash=key_hash, name=name, role=role)
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return raw, api_key
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_api_key_with_value(raw_key: str, name: str, role: str = "candidate") -> ApiKey:
    key_hash = hash_key(raw_key)
    key_prefix = raw_key[:8]
    db = SessionLocal()
    try:
        existing = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if existing:
            return existing
        api_key = ApiKey(key_prefix=key_prefix, key_hash=key_hash, name=name, role=role)
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def list_api_keys() -> list[ApiKey]:
    db = SessionLocal()
    try:
        return db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    finally:
        db.close()


def revoke_api_key(key_id: int) -> bool:
    db = SessionLocal()
    try:
        key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
        if not key:
            return False
        key.is_active = False
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
