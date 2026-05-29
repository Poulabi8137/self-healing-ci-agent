from app.api.pr_router import PRCreateRequest, router


class TestPRRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_pr_create_request_defaults(self):
        req = PRCreateRequest(repository_name="test-repo", logs="error log")
        assert req.repository_name == "test-repo"
        assert req.logs == "error log"
        assert req.dry_run is True
        assert req.approved is False

    def test_pr_create_request_custom(self):
        req = PRCreateRequest(
            repository_name="owner/repo",
            logs="logs",
            dry_run=False,
            approved=True,
        )
        assert req.dry_run is False
        assert req.approved is True
