from app.dashboard.metrics_collector import collect_workflow_metrics, collect_repository_metrics


class TestCollectWorkflowMetrics:
    def test_returns_structured_dict(self):
        result = collect_workflow_metrics()
        assert isinstance(result, dict)
        assert "total_runs" in result
        assert "total_successful" in result
        assert "total_failed" in result
        assert "total_retries" in result
        assert "total_reviews" in result
        assert "total_prs" in result
        assert "total_prs_real" in result
        assert "total_prs_simulated" in result

    def test_all_counts_are_integers(self):
        result = collect_workflow_metrics()
        for key in ["total_runs", "total_successful", "total_failed", "total_retries",
                     "total_reviews", "total_prs", "total_prs_real", "total_prs_simulated"]:
            assert isinstance(result[key], int)


class TestCollectRepositoryMetrics:
    def test_returns_list(self):
        result = collect_repository_metrics()
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self):
        result = collect_repository_metrics()
        if result:
            item = result[0]
            assert "repository_name" in item
            assert "total_runs" in item
            assert "successful_runs" in item
            assert "failed_runs" in item
            assert "avg_confidence" in item
            assert "success_rate" in item
