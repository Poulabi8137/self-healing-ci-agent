from app.config.settings import settings


class TestRetryLimits:
    def test_max_retry_attempts_exists(self):
        assert hasattr(settings, "max_retry_attempts")
        assert isinstance(settings.max_retry_attempts, int)

    def test_max_retry_attempts_default(self):
        assert settings.max_retry_attempts == 3

    def test_max_retry_attempts_positive(self):
        assert settings.max_retry_attempts > 0
