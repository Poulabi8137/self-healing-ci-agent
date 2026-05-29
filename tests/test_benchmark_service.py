from app.dashboard.benchmark_service import get_benchmark_summary, get_repository_benchmark


class TestGetBenchmarkSummary:
    def test_returns_structured_dict(self):
        summary = get_benchmark_summary()
        assert "system_health" in summary
        assert "validation" in summary
        assert "review" in summary
        assert "confidence" in summary
        assert "repositories" in summary

    def test_system_health_keys(self):
        summary = get_benchmark_summary()
        health = summary["system_health"]
        assert "total_workflow_runs" in health
        assert "overall_success_rate" in health
        assert "average_retries_per_run" in health


class TestGetRepositoryBenchmark:
    def test_unknown_repository(self):
        result = get_repository_benchmark("nonexistent-repo")
        assert "repository_name" in result
        assert result["repository_name"] == "nonexistent-repo"
