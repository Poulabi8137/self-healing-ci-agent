from app.api.router import router


class TestHealthRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_routes_are_get(self):
        for route in router.routes:
            methods = getattr(route, "methods", set())
            assert "GET" in methods

    def test_health_route_exists(self):
        paths = [route.path for route in router.routes]
        assert "/health" in paths

    def test_version_route_exists(self):
        paths = [route.path for route in router.routes]
        assert "/version" in paths
