from app.dashboard.report_generator import generate_report


class TestGenerateReport:
    def test_full_report(self):
        report = generate_report("full")
        assert report["report_type"] == "full"
        assert "overview" in report
        assert "validation" in report
        assert "review" in report
        assert "pr" in report
        assert "repositories" in report

    def test_summary_report(self):
        report = generate_report("summary")
        assert report["report_type"] == "summary"
        assert "success_rate" in report
        assert "avg_retries" in report
        assert "validation_pass_rate" in report

    def test_repositories_report(self):
        report = generate_report("repositories")
        assert report["report_type"] == "repositories"
        assert "repositories" in report

    def test_report_has_generated_at(self):
        report = generate_report("summary")
        assert "generated_at" in report
        assert "system_version" in report
