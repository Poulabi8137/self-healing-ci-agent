"""Circuit breaker pattern for external API resilience.

Prevents cascading failures by stopping requests to a failing service
after a configurable threshold of consecutive failures.
"""

import asyncio
import time
from enum import Enum
from typing import Optional

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """State machine that tracks external service health.

    States:
        CLOSED   — normal operation, requests pass through
        OPEN     — failure threshold exceeded, requests are rejected immediately
        HALF_OPEN — recovery timeout elapsed, one test request allowed

    Thread-safe for async use. Uses asyncio lock for state transitions.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        half_open_max_requests: Optional[int] = None,
    ):
        self.name = name
        self._failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self._recovery_timeout = recovery_timeout or settings.circuit_breaker_recovery_timeout
        self._half_open_max_requests = half_open_max_requests or settings.circuit_breaker_half_open_max_requests

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_requests = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def __aenter__(self) -> "CircuitBreaker":
        await self._check_state()
        if self._state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable (recovery in {self._remaining_cooldown():.0f}s)."
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._on_success()
        elif exc_type is CircuitBreakerOpenError:
            pass
        else:
            await self._on_failure()

    async def _check_state(self):
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                    logger.info(
                        "Circuit breaker '%s' transitioning OPEN -> HALF_OPEN "
                        "(recovery timeout elapsed)",
                        self.name,
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_requests = 0

    async def _on_success(self):
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_requests += 1
                if self._half_open_requests >= self._half_open_max_requests:
                    logger.info(
                        "Circuit breaker '%s' transitioning HALF_OPEN -> CLOSED "
                        "(%d/%d successful test requests)",
                        self.name,
                        self._half_open_requests,
                        self._half_open_max_requests,
                    )
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_requests = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker '%s' transitioning HALF_OPEN -> OPEN "
                    "(test request failed, %d/%d failures)",
                    self.name,
                    self._failure_count,
                    self._failure_threshold,
                )
                self._state = CircuitState.OPEN
                self._half_open_requests = 0
            elif self._failure_count >= self._failure_threshold:
                logger.warning(
                    "Circuit breaker '%s' transitioning CLOSED -> OPEN "
                    "(%d/%d consecutive failures)",
                    self.name,
                    self._failure_count,
                    self._failure_threshold,
                )
                self._state = CircuitState.OPEN

    def _remaining_cooldown(self) -> float:
        return max(
            0.0,
            self._recovery_timeout - (time.monotonic() - self._last_failure_time),
        )

    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_requests = 0
        logger.info("Circuit breaker '%s' manually reset to CLOSED", self.name)


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is OPEN and rejects a request."""
