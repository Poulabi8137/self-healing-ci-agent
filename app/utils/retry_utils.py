import asyncio
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def retry(
    max_retries: Optional[int] = None,
    delay: Optional[float] = None,
    exceptions: Union[Type[Exception], tuple] = Exception,
):
    max_retries = max_retries or settings.max_retries
    delay = delay or settings.retry_delay

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {str(e)}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {str(e)}")
                    if attempt < max_retries:
                        time.sleep(delay)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
