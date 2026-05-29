from app.api.rag_router import IndexRequest, RetrieveRequest, router


class TestRAGRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    def test_has_post_routes(self):
        post_paths = []
        for route in router.routes:
            methods = getattr(route, "methods", set())
            if "POST" in methods:
                post_paths.append(route.path)
        assert "/index" in post_paths
        assert "/retrieve" in post_paths

    def test_has_get_routes(self):
        get_paths = []
        for route in router.routes:
            methods = getattr(route, "methods", set())
            if "GET" in methods:
                get_paths.append(route.path)
        assert len(get_paths) > 0

    def test_index_request_model(self):
        req = IndexRequest(repo_url="https://github.com/user/repo")
        assert req.repo_url == "https://github.com/user/repo"
        assert req.branch is None
        assert req.chunk_size is None
        assert req.chunk_overlap is None

    def test_index_request_custom(self):
        req = IndexRequest(
            repo_url="https://github.com/user/repo",
            branch="develop",
            chunk_size=1000,
            chunk_overlap=100,
        )
        assert req.branch == "develop"
        assert req.chunk_size == 1000
        assert req.chunk_overlap == 100

    def test_retrieve_request_model(self):
        req = RetrieveRequest(repo_name="user/repo", query="error handling")
        assert req.repo_name == "user/repo"
        assert req.query == "error handling"
        assert req.top_k == 5

    def test_retrieve_request_custom_top_k(self):
        req = RetrieveRequest(repo_name="user/repo", query="test", top_k=10)
        assert req.top_k == 10
