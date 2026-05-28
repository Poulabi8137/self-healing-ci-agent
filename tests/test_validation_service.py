import pytest

from app.validation.validation_service import validate_fix


class TestValidateFix:
    async def test_unknown_repository(self):
        report = await validate_fix(
            repository_name="nonexistent-repo",
            modified_files=None,
        )
        assert report["repository"] == "nonexistent-repo"
        assert "validation_status" in report

    async def test_with_modified_files(self):
        report = await validate_fix(
            repository_name="nonexistent-repo",
            modified_files=["src/main.py", "src/utils.py"],
        )
        assert report["repository"] == "nonexistent-repo"
