3

from app.dashboard.analytics_engine import (
    compute_success_rate,
    compute_average_retries,
    compute_validation_pass_rate,
    compute_average_review_score,
    compute_average_confidence,
    compute_retry_distribution,
    compute_full_analytics,
)


class TestComputeSuccessRate:
    def test_empty_metrics(self):
        assert compute_success_rate({}) == 0.0
        assert compute_success_rate({"total_runs": 0, "total_successful": 0}) == 0.0

    def test_half_success(self):
        metrics = {"total_runs": 10, "total_successful": 5}
        assert compute_success_rate(metrics) == 50.0

    def test_all_success(self):
        metrics = {"total_runs": 5, "total_successful": 5}
        assert compute_success_rate(metrics) == 100.0


class TestComputeAverageRetries:
    def test_empty(self):
        assert compute_average_retries({}) == 0.0

    def test_no_retries(self):
        metrics = {"total_runs": 5, "total_retries": 0}
        assert compute_average_retries(metrics) == 0.0

    def test_some_retries(self):
        metrics = {"total_runs": 10, "total_retries": 5}
        assert compute_average_retries(metrics) == 0.5


class TestComputeValidationPassRate:
    def test_returns_float(self):
        rate = compute_validation_pass_rate()
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 100.0


class TestComputeAverageReviewScore:
    def test_returns_float(self):
        score = compute_average_review_score()
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestComputeAverageConfidence:
    def test_returns_float(self):
        score = compute_average_confidence()
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestComputeRetryDistribution:
    def test_returns_dict(self):
        dist = compute_retry_distribution()
        assert isinstance(dist, dict)


class TestComputeFullAnalytics:
    def test_returns_all_keys(self):
        analytics = compute_full_analytics()
        assert "workflow_metrics" in analytics
        assert "repository_metrics" in analytics
        assert "success_rate" in analytics
        assert "average_retries" in analytics
        assert "validation_pass_rate" in analytics
        assert "average_review_score" in analytics
        assert "average_confidence" in analytics
        assert "retry_distribution" in analytics
        assert "total_repositories" in analytics
