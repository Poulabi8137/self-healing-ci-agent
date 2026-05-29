from app.github.branch_manager import generate_branch_name


class TestGenerateBranchName:
    def test_default_category(self):
        name = generate_branch_name()
        assert name.startswith("fix/")

    def test_custom_category(self):
        name = generate_branch_name(error_category="import_error")
        assert name.startswith("fix/import-error-")

    def test_spaces_in_category(self):
        name = generate_branch_name(error_category="runtime error")
        assert name.startswith("fix/runtime-error-")

    def test_includes_attempt_number(self):
        name = generate_branch_name(error_category="test", attempt_number=3)
        assert name.endswith("-3")
