from app.api.review_router import ReviewRequest, router


class TestReviewRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_review_request_model(self):
        req = ReviewRequest(repository_name="test-repo", logs="error log")
        assert req.repository_name == "test-repo"
        assert req.logs == "error log"
