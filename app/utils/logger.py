import sys
from pathlib import Path

from loguru import logger as _logger

from app.config.settings import settings


def get_logger(name: str = __name__):
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    _logger.remove()

    _logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
        level=settings.log_level.upper(),
        colorize=True,
    )

    _logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    return _logger.bind(name=name)
