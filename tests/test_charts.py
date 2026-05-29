from app.dashboard.charts import (
    get_success_vs_failure_dataset,
    get_retry_distribution_dataset,
    get_review_scores_dataset,
    get_validation_results_dataset,
    get_pr_statistics_dataset,
)


class TestSuccessVsFailureDataset:
    def test_returns_structured_dict(self):
        data = get_success_vs_failure_dataset()
        assert "labels" in data
        assert "values" in data
        assert "colors" in data
        assert len(data["labels"]) == 2
        assert len(data["values"]) == 2


class TestRetryDistributionDataset:
    def test_returns_structured_dict(self):
        data = get_retry_distribution_dataset()
        assert "labels" in data
        assert "values" in data


class TestReviewScoresDataset:
    def test_returns_structured_dict(self):
        data = get_review_scores_dataset()
        assert "categories" in data
        assert "scores" in data
        assert "average" in data
        assert len(data["categories"]) == 5


class TestValidationResultsDataset:
    def test_returns_structured_dict(self):
        data = get_validation_results_dataset()
        assert "labels" in data
        assert "values" in data


class TestPRStatisticsDataset:
    def test_returns_structured_dict(self):
        data = get_pr_statistics_dataset()
        assert "labels" in data
        assert "values" in data
