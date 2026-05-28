from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    from app.database.models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
