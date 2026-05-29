from app.api.validation_router import ValidationRequest, router


class TestValidationRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_routes_are_post(self):
        for route in router.routes:
            methods = getattr(route, "methods", set())
            assert "POST" in methods

    def test_run_route_path(self):
        paths = [route.path for route in router.routes]
        assert "/run" in paths

    def test_request_model_valid(self):
        req = ValidationRequest(repository_name="test-repo", logs="test logs")
        assert req.repository_name == "test-repo"
        assert req.logs == "test logs"
