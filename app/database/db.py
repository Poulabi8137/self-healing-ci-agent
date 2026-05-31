from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from alembic.config import Config
from alembic import command

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


def _run_alembic_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations up to date.")


def _verify_migrations():
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext

    conn = engine.connect()
    try:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        script = ScriptDirectory.from_config(Config("alembic.ini"))
        head_rev = script.get_current_head()

        if current_rev == head_rev:
            logger.info(f"Migration verified at revision: {current_rev}")
        elif current_rev is None:
            logger.warning("No migration revision found — running migrations...")
            _run_alembic_migrations()
        else:
            logger.warning(f"Database at revision {current_rev}, head is {head_rev} — upgrading...")
            _run_alembic_migrations()
    finally:
        conn.close()


def init_db():
    from app.database.models import Base as ModelsBase
    import app.auth.models
    import app.queue.models

    try:
        _verify_migrations()
    except Exception as e:
        logger.warning(f"Migration verification failed ({str(e)}), falling back to create_all")
        ModelsBase.metadata.create_all(bind=engine)
        logger.info("Database tables created via create_all fallback.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
