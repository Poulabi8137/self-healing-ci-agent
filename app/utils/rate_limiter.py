"""Sliding-window in-memory rate limiter middleware."""
import re
import time
import hashlib
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request

from app.config.settings import settings

_window_store: dict[str, list[float]] = defaultdict(list)


def reset_rate_limits():
    _window_store.clear()


def _client_key(request: Request) -> str:
    xfwd = request.headers.get("X-Forwarded-For", "")
    client = xfwd.split(",")[0].strip() if xfwd else (request.client.host if request.client else "unknown")
    api_key = request.headers.get("X-API-Key", "")
    raw = f"{api_key}:{client}" if api_key else client
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _clean(key: str, window: float):
    now = time.time()
    _window_store[key] = [t for t in _window_store[key] if now - t < window]


LIMITS: list[tuple[re.Pattern, str, int, float]] = [
    # (path_pattern, method, max_requests, window_seconds)
    (re.compile(r"^/health$"), "GET", 30, 60),
    (re.compile(r"^/version$"), "GET", 30, 60),
    (re.compile(r"^/dashboard/"), "GET", 30, 60),
    (re.compile(r"^/tasks/\d+$"), "GET", 30, 60),
    (re.compile(r"^/tasks/$"), "GET", 30, 60),
    (re.compile(r"^/tasks/submit$"), "POST", 10, 60),
    (re.compile(r"^/analysis/"), "POST", 10, 60),
    (re.compile(r"^/fix/"), "POST", 10, 60),
    (re.compile(r"^/validation/"), "POST", 10, 60),
    (re.compile(r"^/retry/"), "POST", 5, 60),
    (re.compile(r"^/review/"), "POST", 10, 60),
    (re.compile(r"^/pr/"), "POST", 5, 60),
    (re.compile(r"^/rag/index$"), "POST", 5, 60),
    (re.compile(r"^/rag/retrieve$"), "POST", 10, 60),
    (re.compile(r"^/rag/index/"), "GET", 30, 60),
    (re.compile(r"^/auth/keys$"), "POST", 5, 60),
    (re.compile(r"^/auth/keys/\d+$"), "DELETE", 5, 60),
    (re.compile(r"^/auth/keys$"), "GET", 10, 60),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limiting_enabled:
            return await call_next(request)

        path = request.url.path
        method = request.method
        max_req, window = 0, 60.0
        for pat, meth, mr, w in LIMITS:
            if pat.match(path) and (meth == "*" or meth == method):
                max_req, window = mr, w
                break
        if max_req == 0:
            return await call_next(request)

        k = _client_key(request)
        _clean(k, window)
        count = len(_window_store[k])
        if count >= max_req:
            body = {"detail": "Rate limit exceeded. Try again later.", "retry_after_seconds": int(window)}
            resp = JSONResponse(status_code=429, content=body)
            resp.headers["X-RateLimit-Limit"] = str(max_req)
            resp.headers["X-RateLimit-Remaining"] = "0"
            resp.headers["Retry-After"] = str(int(window))
            return resp

        _window_store[k].append(time.time())
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(max_req - count - 1)
        return response
