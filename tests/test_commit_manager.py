import pytest

from app.github.commit_manager import generate_commit_message, create_commit


class TestGenerateCommitMessage:
    def test_basic_message(self):
        msg = generate_commit_message("Added input validation", root_cause="Missing input check")
        assert msg.startswith("fix: Added input validation")
        assert "Missing input check" in msg

    def test_with_modified_files(self):
        msg = generate_commit_message(
            "Fixed import error",
            modified_files=["src/main.py", "src/utils.py"],
        )
        assert "src/main.py" in msg
        assert "src/utils.py" in msg

    def test_short_summary(self):
        msg = generate_commit_message("Fix")
        assert "fix: Fix" in msg


@pytest.mark.asyncio
class TestCreateCommit:
    async def test_dry_run_valid(self):
        result = await create_commit("fix: resolved error", dry_run=True)
        assert result["committed"] is True
        assert result["dry_run"] is True

    async def test_dry_run_empty_message(self):
        result = await create_commit("", dry_run=True)
        assert result["committed"] is False
        assert "error" in result

    async def test_real_mode_not_yet_implemented(self):
        result = await create_commit("fix: resolved error", dry_run=False)
        assert result["committed"] is False
        assert result["dry_run"] is False
