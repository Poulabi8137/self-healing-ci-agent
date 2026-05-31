import asyncio
import inspect
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def retry(
    max_retries: Optional[int] = None,
    delay: Optional[float] = None,
    backoff_factor: Optional[float] = None,
    jitter: Optional[float] = None,
    exceptions: Union[Type[Exception], tuple] = Exception,
):
    """Decorator that retries a function with exponential backoff and jitter.

    Args:
        max_retries: Maximum number of retry attempts (default: settings.max_retries).
        delay: Base delay in seconds between retries (default: settings.retry_delay).
        backoff_factor: Multiplier applied to delay after each attempt
                        (default: settings.retry_backoff_factor).
        jitter: Maximum random jitter fraction to add/subtract from delay
                (default: settings.retry_jitter).
        exceptions: Exception type(s) that trigger a retry.

    The actual delay before attempt N is:
        delay * (backoff_factor ** (N - 1)) + random.uniform(-jitter, jitter) * delay
    """
    max_retries = max_retries or settings.max_retries
    base_delay = delay or settings.retry_delay
    backoff_factor = backoff_factor or settings.retry_backoff_factor
    jitter = jitter or settings.retry_jitter

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    if attempt < max_retries:
                        sleep_time = _compute_delay(attempt, base_delay, backoff_factor, jitter)
                        await asyncio.sleep(sleep_time)
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
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    if attempt < max_retries:
                        sleep_time = _compute_delay(attempt, base_delay, backoff_factor, jitter)
                        time.sleep(sleep_time)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _compute_delay(
    attempt: int,
    base_delay: float,
    backoff_factor: float,
    jitter: float,
) -> float:
    """Compute the delay before the given attempt with exponential backoff + jitter.

    Formula:
        delay = base_delay * (backoff_factor ** (attempt - 1))
        jitter_amount = random.uniform(-jitter, jitter) * base_delay
        total = max(0.0, delay + jitter_amount)
    """
    exponential_delay = base_delay * (backoff_factor ** (attempt - 1))
    jitter_amount = random.uniform(-jitter, jitter) * base_delay
    return max(0.0, exponential_delay + jitter_amount)
