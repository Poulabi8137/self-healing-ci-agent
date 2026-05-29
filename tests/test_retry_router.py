from app.api.retry_router import RetryRequest, router


class TestRetryRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_retry_request_model(self):
        req = RetryRequest(repository_name="test-repo", logs="error log")
        assert req.repository_name == "test-repo"
        assert req.logs == "error log"
