import functools
import time

from app.utils.logger import get_logger

logger = get_logger(__name__)


def ttl_cache(ttl_seconds: int = 30, maxsize: int = 128):
    """Decorator that caches function results with a TTL.

    Args:
        ttl_seconds: Time-to-live in seconds before cache expires.
        maxsize: Maximum number of cached results (passed to lru_cache).

    Uses a combination of lru_cache and a timestamp-based expiry.
    The underlying lru_cache stores (timestamp, result) tuples.
    """
    def decorator(func):
        @functools.lru_cache(maxsize=maxsize)
        def _cached(*args, **kwargs):
            return (time.time(), func(*args, **kwargs))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = None
            try:
                cache_key = args + tuple(sorted(kwargs.items()))
                result = _cached(*args, **kwargs)
                elapsed = time.time() - result[0]
                if elapsed < ttl_seconds:
                    return result[1]
                _cached.cache_clear()
                result = _cached(*args, **kwargs)
                return result[1]
            except Exception:
                _cached.cache_clear()
                return func(*args, **kwargs)

        def invalidate():
            _cached.cache_clear()
            logger.debug(f"Cache invalidated for {func.__name__}")

        wrapper.invalidate = invalidate
        return wrapper
    return decorator
