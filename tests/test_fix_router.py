from app.api.fix_router import FixGenerationRequest, router


class TestFixRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_routes_are_post(self):
        for route in router.routes:
            methods = getattr(route, "methods", set())
            assert "POST" in methods

    def test_generate_route_path(self):
        paths = [route.path for route in router.routes]
        assert "/generate" in paths

    def test_request_model_valid(self):
        req = FixGenerationRequest(repository_name="test-repo", logs="build error")
        assert req.repository_name == "test-repo"
        assert req.logs == "build error"
