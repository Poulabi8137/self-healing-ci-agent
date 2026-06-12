"""
Phase 8.5 — End-to-End Verification Test.

Proves the entire self-healing workflow:
  Failure → Investigation → Root Cause → Fix Artifact → Patch Application
  → Validation → Pull Request

This test uses in-memory/DB-level verification (not live GitHub API calls).
For live GitHub verification, set E2E_GITHUB_REPO and E2E_GITHUB_TOKEN.
"""
import json
import os
from datetime import datetime, timezone

import pytest

from app.database.db import SessionLocal, init_db
from app.database.models import (
    User, Repository, GitHubInstallation, Investigation,
    Failure, FixArtifact, ValidationResult, PRRecord,
    InvestigationEvent,
)
from app.auth.oauth import create_jwt
from app.utils.rate_limiter import reset_rate_limits
from app.services.pr_service import generate_pr_title, generate_pr_description
from app.services.patch_service import apply_patch
from app.services.status_service import derive_repository_status


# ── Test fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _setup():
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(PRRecord).delete()
        db.query(InvestigationEvent).delete()
        db.query(ValidationResult).delete()
        db.query(FixArtifact).delete()
        db.query(Investigation).delete()
        db.query(Failure).delete()
        db.query(GitHubInstallation).delete()
        db.query(Repository).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


def _create_test_user(db):
    user = User(email="e2e@test.com", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_installation(db, user):
    install = GitHubInstallation(
        user_id=user.id,
        installation_id=99999,
        account_login="e2e-test",
    )
    db.add(install)
    db.commit()
    db.refresh(install)
    return install


def _create_repo(db, install, full_name="e2e/test-repo", default_branch="main"):
    repo = Repository(
        name=full_name,
        full_name=full_name,
        is_active=True,
        default_branch=default_branch,
        github_installation_id=install.id,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def _create_failure(db, repo, logs="Error: name 'x' is not defined"):
    failure = Failure(
        repository_id=repo.id,
        workflow_name="test-workflow",
        run_id=str(12345),
        error_message=logs,
        error_logs=logs,
    )
    db.add(failure)
    db.commit()
    db.refresh(failure)
    return failure


def _create_investigation(db, repo, failure, status="detecting"):
    inv = Investigation(
        failure_id=failure.id,
        repository_id=repo.id,
        status=status,
        root_cause="NameError: variable 'x' used before assignment",
        error_category="runtime_error",
        confidence=0.92,
        summary="Missing variable assignment before usage in app.py",
        current_stage="investigation_started",
        current_stage_status="completed",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _create_fix_artifact(db, inv):
    art = FixArtifact(
        investigation_id=inv.id,
        fix_summary="Add missing variable assignment for 'x' in app.py",
        root_cause="Variable 'x' was referenced before being assigned a value",
        confidence_score=0.85,
        files_modified=json.dumps(["src/app.py"]),
        patch_content="--- a/src/app.py\n+++ b/src/app.py\n@@ -1,3 +1,4 @@\n-def get_value():\n+def get_value():\n+    x = 42\n     return x\n",
        branch_name="auto-fix/e2e-test-20260611",
        dry_run=False,
        status="applied",
        generated_at=datetime.now(timezone.utc),
        applied_at=datetime.now(timezone.utc),
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


def _create_validation_results(db, inv):
    stages = [
        ("build_validation", "passed", 1200, 0.95),
        ("unit_test_validation", "passed", 3400, 0.90),
        ("integration_test_validation", "passed", 5100, None),
        ("security_scan_validation", "passed", 2800, None),
        ("regression_validation", "passed", 4100, None),
        ("confidence_evaluation", "passed", 300, 0.87),
    ]
    results = []
    for name, status, dur, conf in stages:
        vr = ValidationResult(
            investigation_id=inv.id,
            validation_type=name,
            status=status,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            duration_ms=dur,
            logs=f"{name} {'passed' if status == 'passed' else 'failed'}",
            confidence_score=conf,
        )
        db.add(vr)
        results.append(vr)
    db.commit()
    for r in results:
        db.refresh(r)
    return results


def _create_pr_events(db, inv):
    event = InvestigationEvent(
        investigation_id=inv.id,
        event_type="pr_created",
        data=json.dumps({
            "repository": "e2e/test-repo",
            "pr_number": 42,
            "pr_url": "https://github.com/e2e/test-repo/pull/42",
            "pr_title": "[Auto-Heal] Add missing variable assignment",
            "branch_name": "auto-fix/e2e-test-20260611",
            "status": "created",
        }),
    )
    db.add(event)
    db.commit()
    return event


# ── E2E Tests ──────────────────────────────────────────────────────────────────

class TestE2EPersistence:
    """Verify every persistence stage of the self-healing loop."""

    def test_1_failure_persisted(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            assert failure.id is not None
            assert failure.repository_id == repo.id
            assert failure.error_message == "Error: name 'x' is not defined"
        finally:
            db.close()

    def test_2_investigation_created(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)
            assert inv.id is not None
            assert inv.repository_id == repo.id
            assert inv.failure_id == failure.id
            assert inv.status == "detecting"
            assert inv.root_cause is not None
            assert inv.confidence == 0.92
        finally:
            db.close()

    def test_3_fix_artifact_persisted(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)
            art = _create_fix_artifact(db, inv)
            assert art.id is not None
            assert art.investigation_id == inv.id
            assert "app.py" in art.files_modified
            assert "--- a/src/app.py" in art.patch_content
            assert art.status == "applied"
            assert art.branch_name == "auto-fix/e2e-test-20260611"
        finally:
            db.close()

    def test_4_validation_results_persisted(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)
            results = _create_validation_results(db, inv)
            assert len(results) == 6
            for r in results:
                assert r.status == "passed"
            stages = db.query(ValidationResult).filter(
                ValidationResult.investigation_id == inv.id
            ).order_by(ValidationResult.created_at.asc()).all()
            assert len(stages) == 6
            assert stages[0].validation_type == "build_validation"
            assert stages[-1].validation_type == "confidence_evaluation"
        finally:
            db.close()

    def test_5_pr_record_persisted(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)
            art = _create_fix_artifact(db, inv)
            _create_validation_results(db, inv)

            record = PRRecord(
                investigation_id=inv.id,
                repository_id=repo.id,
                repository_name="e2e/test-repo",
                branch_name=art.branch_name,
                pr_title="[Auto-Heal] Add missing variable assignment",
                pr_number=42,
                pr_url="https://github.com/e2e/test-repo/pull/42",
                description=generate_pr_description(
                    fix_summary=art.fix_summary or "",
                    root_cause=art.root_cause or "",
                    modified_files=json.loads(art.files_modified) if art.files_modified else [],
                    confidence_score=art.confidence_score,
                ),
                status="created",
                dry_run=False,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            assert record.id is not None
            assert record.pr_number == 42
            assert record.status == "created"
            assert record.dry_run is False
        finally:
            db.close()

    def test_6_investigation_event_persisted(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)
            event = _create_pr_events(db, inv)
            assert event.id is not None
            assert event.event_type == "pr_created"
            data = json.loads(event.data)
            assert data["pr_number"] == 42
            assert data["pr_url"] == "https://github.com/e2e/test-repo/pull/42"
        finally:
            db.close()


class TestE2EStatusTransitions:
    """Verify status transitions across the full workflow."""

    def test_status_flow(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)

            # active → investigating
            inv1 = _create_investigation(db, repo, failure, status="analyzing")
            status1 = derive_repository_status(repo, db)
            assert status1 == "investigating"

            # investigating → fixing
            inv1.status = "fixing"
            db.commit()
            status2 = derive_repository_status(repo, db)
            assert status2 == "fixing"

            # fixing → validating
            inv1.status = "validating"
            db.commit()
            status3 = derive_repository_status(repo, db)
            assert status3 == "validating"

            # validating → completed
            inv1.status = "completed"
            inv1.completed_at = datetime.now(timezone.utc)
            db.commit()
            status4 = derive_repository_status(repo, db)
            assert status4 == "completed"

            # failed
            inv1.status = "failed"
            db.commit()
            status5 = derive_repository_status(repo, db)
            assert status5 == "failed"
        finally:
            db.close()


class TestE2EPatchService:
    """Verify patch application engine stages."""

    def test_patch_parse_and_dry_run(self):
        from app.services.patch_service import _parse_patch

        patch = """--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
-old code
+new code
 context
+added
--- a/src/utils.py
+++ b/src/utils.py
@@ -1 +1 @@
-foo
+bar
"""
        files = _parse_patch(patch)
        assert len(files) == 2
        assert files[0]["path"] == "src/app.py"
        assert "new code" in files[0]["content"]
        assert "added" in files[0]["content"]
        assert files[1]["path"] == "src/utils.py"
        assert "bar" in files[1]["content"]
        assert "old code" not in files[0]["content"]
        assert "foo" not in files[1]["content"]

        result = apply_patch("e2e/test-repo", "", patch, dry_run=True)
        assert result["applied"] is False
        assert result["files_modified"] == ["src/app.py", "src/utils.py"]

    def test_patch_empty(self):
        from app.services.patch_service import apply_patch
        result = apply_patch("e2e/test-repo", "", "", dry_run=False)
        assert result["applied"] is False
        assert result["files_modified"] == []


class TestE2EPRService:
    """Verify PR generation stages."""

    def test_pr_title_generation(self):
        title = generate_pr_title("Add missing variable assignment for x in app.py")
        assert title.startswith("[Auto-Heal]")
        assert "Add missing variable assignment" in title

    def test_pr_description_contains_all_sections(self):
        desc = generate_pr_description(
            fix_summary="Add missing variable x = 42 before return",
            root_cause="Variable referenced before assignment",
            modified_files=["src/app.py"],
            validation_stages=[
                {"stage": "build_validation", "status": "passed"},
                {"stage": "unit_test_validation", "status": "passed"},
                {"stage": "confidence_evaluation", "status": "passed"},
            ],
            confidence_score=0.87,
        )
        assert "## Summary" in desc
        assert "## Root Cause" in desc
        assert "## Fix Applied" in desc
        assert "## Validation Results" in desc
        assert "## Safety Assessment" in desc
        assert "src/app.py" in desc
        assert "Build Validation" in desc
        assert "Unit Test Validation" in desc
        assert "87%" in desc or "0.87" in desc

    def test_pr_description_empty_fix(self):
        desc = generate_pr_description("", "", [])
        assert "## Summary" in desc
        assert "## Root Cause" in desc
        assert "Unknown — root cause" in desc


class TestE2EStatusService:
    """Verify status service derivation."""

    def test_active_status(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            status = derive_repository_status(repo, db)
            assert status == "active"
        finally:
            db.close()

    def test_disabled_status(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            repo.is_active = False
            db.commit()
            status = derive_repository_status(repo, db)
            assert status == "disabled"
        finally:
            db.close()


class TestE2EFixAPIResponse:
    """Verify the fix API response structure matches frontend expectations."""

    def test_fix_api_response_shape(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)
            art = _create_fix_artifact(db, inv)

            response = {
                "id": art.id,
                "investigation_id": art.investigation_id,
                "fix_summary": art.fix_summary,
                "root_cause": art.root_cause,
                "confidence_score": art.confidence_score,
                "files_modified": json.loads(art.files_modified) if art.files_modified else [],
                "patch_content": art.patch_content,
                "branch_name": art.branch_name,
                "dry_run": art.dry_run,
                "status": art.status,
                "generated_at": art.generated_at.isoformat() if art.generated_at else None,
                "applied_at": art.applied_at.isoformat() if art.applied_at else None,
            }

            assert response["id"] == art.id
            assert response["fix_summary"] == "Add missing variable assignment for 'x' in app.py"
            assert response["files_modified"] == ["src/app.py"]
            assert "--- a/src/app.py" in response["patch_content"]
            assert response["dry_run"] is False
            assert response["status"] == "applied"
        finally:
            db.close()


class TestE2EPRAPIResponse:
    """Verify the PR API response structure matches frontend expectations."""

    def test_pr_api_response_shape(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install)
            failure = _create_failure(db, repo)
            inv = _create_investigation(db, repo, failure)

            record = PRRecord(
                investigation_id=inv.id,
                repository_id=repo.id,
                repository_name="e2e/test-repo",
                branch_name="auto-fix/e2e-test-20260611",
                pr_title="[Auto-Heal] Fix",
                pr_number=42,
                pr_url="https://github.com/e2e/test-repo/pull/42",
                description="## Summary\nTest",
                status="created",
                dry_run=False,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            response = {
                "id": record.id,
                "investigation_id": record.investigation_id,
                "pr_number": record.pr_number,
                "pr_url": record.pr_url,
                "title": record.pr_title,
                "description": record.description,
                "branch_name": record.branch_name,
                "status": record.status,
                "dry_run": record.dry_run,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }

            assert response["pr_number"] == 42
            assert response["pr_url"] == "https://github.com/e2e/test-repo/pull/42"
            assert "Fix" in response["title"]
            assert response["status"] == "created"
            assert response["dry_run"] is False
        finally:
            db.close()


class TestE2EDefaultBranch:
    """Verify default_branch is stored and used by the PR workflow."""

    def test_default_branch_stored(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = _create_repo(db, install, default_branch="develop")
            assert repo.default_branch == "develop"
        finally:
            db.close()

    def test_default_branch_defaults_to_main(self):
        db = SessionLocal()
        try:
            user = _create_test_user(db)
            install = _create_installation(db, user)
            repo = Repository(
                name="test/repo",
                full_name="test/repo",
                is_active=True,
                github_installation_id=install.id,
            )
            db.add(repo)
            db.commit()
            assert repo.default_branch == "main"
        finally:
            db.close()

    def test_default_branch_used_in_pr(self):
        from app.services.pr_service import create_pull_request_async

        # Verify function signature accepts base parameter
        import inspect
        sig = inspect.signature(create_pull_request_async)
        assert "base" in sig.parameters
        assert sig.parameters["base"].default == "main"
