"""Tests for retry utility with exponential backoff and jitter."""
import asyncio
from unittest.mock import patch

import pytest

from app.utils.retry_utils import retry, _compute_delay


class TestComputeDelay:
    def test_exponential_backoff_increases(self):
        d1 = _compute_delay(1, base_delay=1.0, backoff_factor=2.0, jitter=0.0)
        d2 = _compute_delay(2, base_delay=1.0, backoff_factor=2.0, jitter=0.0)
        d3 = _compute_delay(3, base_delay=1.0, backoff_factor=2.0, jitter=0.0)
        assert d1 == 1.0
        assert d2 == 2.0
        assert d3 == 4.0

    def test_jitter_adds_variation(self):
        delays = [_compute_delay(1, base_delay=10.0, backoff_factor=1.0, jitter=0.5) for _ in range(100)]
        min_d, max_d = min(delays), max(delays)
        assert min_d >= 5.0
        assert max_d <= 15.0
        assert max_d - min_d > 0.5

    def test_delay_never_negative(self):
        d = _compute_delay(1, base_delay=1.0, backoff_factor=2.0, jitter=10.0)
        assert d >= 0.0


class TestRetryDecorator:
    @pytest.mark.asyncio
    async def test_async_retry_succeeds_eventually(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01, backoff_factor=1.0, jitter=0.0)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "success"

        result = await flaky()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_exhausted(self):
        call_count = 0

        @retry(max_retries=2, delay=0.01, backoff_factor=1.0, jitter=0.0)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            await always_fails()
        assert call_count == 2

    def test_sync_retry_succeeds_eventually(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01, backoff_factor=1.0, jitter=0.0)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("not yet")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert call_count == 3

    def test_sync_retry_exhausted(self):
        call_count = 0

        @retry(max_retries=2, delay=0.01, backoff_factor=1.0, jitter=0.0)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("never")

        with pytest.raises(RuntimeError, match="never"):
            always_fails()
        assert call_count == 2

    def test_retry_respects_exception_filter(self):
        @retry(max_retries=2, delay=0.01, backoff_factor=1.0, jitter=0.0, exceptions=ValueError)
        def only_value_error():
            raise TypeError("wrong exception")

        with pytest.raises(TypeError):
            only_value_error()

    @pytest.mark.asyncio
    async def test_async_no_retry_on_success(self):
        call_count = 0

        @retry(max_retries=5, delay=0.01, backoff_factor=1.0, jitter=0.0)
        async def works_first_time():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await works_first_time()
        assert result == "ok"
        assert call_count == 1
