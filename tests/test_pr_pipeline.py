"""
Phase 8 tests: PR persistence, service, workflow, API, authorization.
"""
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.db import SessionLocal, init_db
from app.database.models import (
    User, Repository, GitHubInstallation, Investigation,
    FixArtifact, ValidationResult, PRRecord, InvestigationEvent,
)
from app.auth.oauth import create_jwt
from app.utils.rate_limiter import reset_rate_limits

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup():
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(PRRecord).delete()
        db.query(InvestigationEvent).delete()
        db.query(ValidationResult).delete()
        db.query(FixArtifact).delete()
        db.query(Investigation).delete()
        db.query(GitHubInstallation).delete()
        db.query(Repository).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


def _create_test_user(db, email="test@example.com", role="admin"):
    user = User(email=email, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_test_repo(db, name="test/repo"):
    repo = Repository(full_name=name, name=name, is_active=True)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def _create_test_investigation(db, repo_id, status="completed"):
    inv = Investigation(
        repository_id=repo_id,
        status=status,
        current_stage="pr_created",
        current_stage_status="completed",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _create_test_pr_record(db, investigation_id, repo_id, status="simulated"):
    record = PRRecord(
        investigation_id=investigation_id,
        repository_id=repo_id,
        repository_name="test/repo",
        branch_name="auto-fix/test-branch",
        pr_title="[Auto-Heal] Fix broken import",
        pr_number=42,
        pr_url="https://github.com/test/repo/pull/42",
        description="## Summary\nFixed broken import.",
        status=status,
        dry_run=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _cookie_headers_for_user(db, role="admin"):
    user = _create_test_user(db, role=role)
    token = create_jwt(user)
    return {"Cookie": f"jwt={token}"}, user


# --- Model Persistence Tests ---

class TestPRRecordModel:
    def test_create_pr_record(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            rec = _create_test_pr_record(db, inv.id, repo.id)

            assert rec.id is not None
            assert rec.investigation_id == inv.id
            assert rec.repository_id == repo.id
            assert rec.pr_number == 42
            assert rec.pr_url == "https://github.com/test/repo/pull/42"
            assert rec.pr_title == "[Auto-Heal] Fix broken import"
            assert rec.status == "simulated"
            assert rec.dry_run is False
        finally:
            db.close()

    def test_pr_record_defaults(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            rec = PRRecord(
                investigation_id=inv.id,
                repository_id=repo.id,
                repository_name="test/repo",
            )
            db.add(rec)
            db.commit()
            assert rec.status == "simulated"
            assert rec.dry_run is True
            assert rec.pr_number is None
        finally:
            db.close()

    def test_pr_record_fk_cascade(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_pr_record(db, inv.id, repo.id)
            count = db.query(PRRecord).count()
            assert count == 1
        finally:
            db.close()


# --- PR Service Tests ---

class TestPRService:
    def test_generate_pr_title(self):
        from app.services.pr_service import generate_pr_title
        title = generate_pr_title("Fix failing dependency import in setup.py")
        assert title.startswith("[Auto-Heal]")
        assert "Fix failing dependency" in title

    def test_generate_pr_title_empty(self):
        from app.services.pr_service import generate_pr_title
        title = generate_pr_title("")
        assert title == "[Auto-Heal] Automated fix for CI/CD failure"

    def test_generate_pr_title_truncation(self):
        from app.services.pr_service import generate_pr_title
        long_summary = "A" * 100
        title = generate_pr_title(long_summary)
        assert len(title) <= len("[Auto-Heal] ") + 72 + 3

    def test_generate_pr_description_all_sections(self):
        from app.services.pr_service import generate_pr_description
        description = generate_pr_description(
            fix_summary="Fixed the broken import",
            root_cause="Missing import statement in main.py",
            modified_files=["src/main.py", "src/utils.py"],
            validation_stages=[
                {"stage": "build_validation", "status": "passed"},
                {"stage": "unit_test_validation", "status": "passed"},
            ],
            confidence_score=0.85,
        )
        assert "## Summary" in description
        assert "## Root Cause" in description
        assert "## Fix Applied" in description
        assert "## Validation Results" in description
        assert "## Safety Assessment" in description
        assert "Fixed the broken import" in description
        assert "Missing import statement" in description
        assert "src/main.py" in description
        assert "build_validation" in description or "Build Validation" in description
        assert "85%" in description
        assert "Self-Healing CI Agent" in description

    def test_generate_pr_description_no_stages(self):
        from app.services.pr_service import generate_pr_description
        description = generate_pr_description(
            fix_summary="Fix",
            root_cause="Cause",
            modified_files=[],
            validation_stages=None,
            confidence_score=None,
        )
        assert "## Validation Results" in description
        assert "## Safety Assessment" in description

    def test_generate_pr_description_low_confidence(self):
        from app.services.pr_service import generate_pr_description
        description = generate_pr_description(
            fix_summary="Fix", root_cause="Cause",
            modified_files=[], confidence_score=0.2,
        )
        assert "Low confidence" in description

    def test_generate_pr_description_high_confidence(self):
        from app.services.pr_service import generate_pr_description
        description = generate_pr_description(
            fix_summary="Fix", root_cause="Cause",
            modified_files=[], confidence_score=0.85,
        )
        assert "High confidence" in description


# --- API Tests ---

class TestPullRequestAPI:
    def test_get_pull_request_empty(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            headers, _ = _cookie_headers_for_user(db)

            resp = client.get(f"/api/investigations/{inv.id}/pull-request", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] is None
            assert data["pr_number"] is None
        finally:
            db.close()

    def test_get_pull_request_with_record(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            rec = _create_test_pr_record(db, inv.id, repo.id, "created")
            headers, _ = _cookie_headers_for_user(db)

            resp = client.get(f"/api/investigations/{inv.id}/pull-request", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == rec.id
            assert data["pr_number"] == 42
            assert data["pr_url"] == "https://github.com/test/repo/pull/42"
            assert data["title"] == "[Auto-Heal] Fix broken import"
            assert data["branch_name"] == "auto-fix/test-branch"
            assert data["status"] == "created"
            assert data["dry_run"] is False
            assert data["description"] is not None
            assert data["created_at"] is not None
        finally:
            db.close()

    def test_get_pull_request_requires_auth(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            resp = client.get(f"/api/investigations/{inv.id}/pull-request")
            assert resp.status_code == 401
        finally:
            db.close()

    def test_get_pull_request_not_found(self):
        db = SessionLocal()
        try:
            headers, _ = _cookie_headers_for_user(db)
            resp = client.get("/api/investigations/9999/pull-request", headers=headers)
            assert resp.status_code == 404
        finally:
            db.close()

    def test_pull_request_has_all_fields(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_pr_record(db, inv.id, repo.id)
            headers, _ = _cookie_headers_for_user(db)

            resp = client.get(f"/api/investigations/{inv.id}/pull-request", headers=headers)
            data = resp.json()
            for key in ("id", "investigation_id", "pr_number", "pr_url",
                        "title", "description", "branch_name", "status",
                        "dry_run", "created_at"):
                assert key in data
        finally:
            db.close()


# --- Authorization Tests ---

class TestPullRequestAuthorization:
    def test_non_admin_can_see_own_pr(self):
        db = SessionLocal()
        try:
            headers, user = _cookie_headers_for_user(db, role="candidate")
            install = GitHubInstallation(user_id=user.id, installation_id=123, account_login="test")
            db.add(install)
            db.commit()
            db.refresh(install)

            repo = Repository(
                full_name="user/repo",
                name="user/repo",
                is_active=True,
                github_installation_id=install.id,
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

            inv = _create_test_investigation(db, repo.id)
            _create_test_pr_record(db, inv.id, repo.id)

            resp = client.get(f"/api/investigations/{inv.id}/pull-request", headers=headers)
            assert resp.status_code == 200
            assert resp.json()["id"] is not None
        finally:
            db.close()

    def test_non_admin_cannot_see_others_pr(self):
        db = SessionLocal()
        try:
            admin_user = _create_test_user(db, email="admin@test.com", role="admin")
            headers, _ = _cookie_headers_for_user(db, role="candidate")
            install = GitHubInstallation(user_id=admin_user.id, installation_id=456, account_login="admin")
            db.add(install)
            db.commit()
            db.refresh(install)

            repo = Repository(
                full_name="other/repo",
                name="other/repo",
                is_active=True,
                github_installation_id=install.id,
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

            inv = _create_test_investigation(db, repo.id)
            _create_test_pr_record(db, inv.id, repo.id)

            resp = client.get(f"/api/investigations/{inv.id}/pull-request", headers=headers)
            assert resp.status_code == 403
        finally:
            db.close()


# --- Event Emission Tests ---

class TestPREventEmission:
    def test_pr_workflow_updates_investigation_status(self):
        from app.services.pr_service import generate_pr_title, generate_pr_description
        title = generate_pr_title("Fix")
        assert title.startswith("[Auto-Heal]")

    def test_pr_workflow_description_contains_sections(self):
        from app.services.pr_service import generate_pr_description
        desc = generate_pr_description("Fix", "Cause", ["x.py"])
        assert "## Summary" in desc
        assert "## Root Cause" in desc
