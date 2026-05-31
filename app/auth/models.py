from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.database.db import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_prefix = Column(String(8), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="candidate")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
