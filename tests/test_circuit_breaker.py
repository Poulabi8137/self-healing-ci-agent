"""Tests for circuit breaker pattern."""
import asyncio

import pytest

from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=1, half_open_max_requests=2)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_transitions_to_open_after_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60, half_open_max_requests=2)
        for _ in range(3):
            with pytest.raises(ConnectionError):
                async with cb:
                    raise ConnectionError("fail")
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60, half_open_max_requests=2)
        with pytest.raises(ConnectionError):
            async with cb:
                raise ConnectionError("fail")
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerOpenError):
            async with cb:
                pass

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05, half_open_max_requests=2)
        with pytest.raises(ConnectionError):
            async with cb:
                raise ConnectionError("fail")
        assert cb.state == CircuitState.OPEN
        await asyncio.sleep(0.06)
        # Entering the context triggers _check_state which transitions OPEN -> HALF_OPEN
        async with cb:
            pass
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_successful_half_open_requests(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05, half_open_max_requests=2)
        with pytest.raises(ConnectionError):
            async with cb:
                raise ConnectionError("fail")
        assert cb.state == CircuitState.OPEN
        await asyncio.sleep(0.06)
        for _ in range(2):
            async with cb:
                pass
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_reopens_on_half_open_failure(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05, half_open_max_requests=2)
        with pytest.raises(ConnectionError):
            async with cb:
                raise ConnectionError("fail")
        await asyncio.sleep(0.06)
        with pytest.raises(ConnectionError):
            async with cb:
                raise ConnectionError("still failing")
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=5, recovery_timeout=60, half_open_max_requests=2)
        for _ in range(3):
            with pytest.raises(ValueError):
                async with cb:
                    raise ValueError("transient")
        assert cb.failure_count == 3
        async with cb:
            pass
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_manual_reset(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60, half_open_max_requests=2)
        cb._failure_count = 10
        cb._state = CircuitState.OPEN
        cb._last_failure_time = 12345.0
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb._last_failure_time == 0.0

    @pytest.mark.asyncio
    async def test_context_manager_success_does_not_raise(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=1, half_open_max_requests=2)
        async with cb:
            result = "ok"
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_context_manager_failure_counts(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=1, half_open_max_requests=2)
        for i in range(2):
            with pytest.raises(ValueError):
                async with cb:
                    raise ValueError(f"fail {i}")
        assert cb.failure_count == 2
