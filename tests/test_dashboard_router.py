from app.api.dashboard_router import router


class TestDashboardRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_routes_are_get(self):
        for route in router.routes:
            methods = getattr(route, "methods", set())
            assert "GET" in methods
