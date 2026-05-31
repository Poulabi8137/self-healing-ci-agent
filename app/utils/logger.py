import sys
import json
from pathlib import Path

from loguru import logger as _logger

from app.config.settings import settings

_sinks_initialized = False


def _json_serialize(record):
    subset = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "module": record["name"],
        "message": record["message"],
    }
    extra = record.get("extra", {})
    if extra:
        subset.update({k: v for k, v in extra.items() if not k.startswith("_")})
    if record.get("exception"):
        subset["exception"] = str(record["exception"])
    return json.dumps(subset, default=str)


def get_logger(name: str = __name__):
    global _sinks_initialized

    if not _sinks_initialized:
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

        if settings.log_json:
            json_log_file = log_dir / "app.jsonl"
            _logger.add(
                json_log_file,
                format=_json_serialize,
                level="DEBUG",
                rotation="50 MB",
                retention="90 days",
                compression="gz",
                serialize=False,
            )

        _sinks_initialized = True

    return _logger.bind(name=name)
