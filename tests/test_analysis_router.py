from app.api.analysis_router import DebugAnalysisRequest, router


class TestAnalysisRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_routes_are_post(self):
        for route in router.routes:
            methods = getattr(route, "methods", set())
            assert "POST" in methods

    def test_debug_route_path(self):
        paths = [route.path for route in router.routes]
        assert "/debug" in paths

    def test_request_model_valid(self):
        req = DebugAnalysisRequest(repository_name="test-repo", logs="error: test failed")
        assert req.repository_name == "test-repo"
        assert req.logs == "error: test failed"

    def test_request_model_empty_logs(self):
        req = DebugAnalysisRequest(repository_name="test-repo", logs="")
        assert req.repository_name == "test-repo"
        assert req.logs == ""
