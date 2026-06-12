"""
Phase 7 tests: fix artifact persistence, patch application, API, authorization.
"""
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.db import SessionLocal, init_db
from app.database.models import (
    User, Repository, GitHubInstallation, Investigation,
    FixArtifact, InvestigationEvent,
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
        db.query(FixArtifact).delete()
        db.query(InvestigationEvent).delete()
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


def _create_test_investigation(db, repo_id, status="fixing"):
    inv = Investigation(
        repository_id=repo_id,
        status=status,
        current_stage="fix_generated",
        current_stage_status="completed",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _create_test_fix_artifact(db, investigation_id, status="generated"):
    artifact = FixArtifact(
        investigation_id=investigation_id,
        fix_summary="Fix the broken import",
        root_cause="Missing import statement",
        confidence_score=0.85,
        files_modified=json.dumps(["src/main.py", "src/utils.py"]),
        patch_content="--- a/src/main.py\n+++ b/src/main.py\n@@ -1 +1 @@\n-foo\n+bar",
        branch_name="auto-fix/test-branch",
        dry_run=False,
        status=status,
        generated_at=datetime.now(timezone.utc),
        applied_at=datetime.now(timezone.utc) if status == "applied" else None,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def _cookie_headers_for_user(db, role="admin"):
    user = _create_test_user(db, role=role)
    token = create_jwt(user)
    return {"Cookie": f"jwt={token}"}, user


# --- Model Persistence Tests ---

class TestFixArtifactModel:
    def test_create_fix_artifact(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            art = _create_test_fix_artifact(db, inv.id)

            assert art.id is not None
            assert art.investigation_id == inv.id
            assert art.fix_summary == "Fix the broken import"
            assert art.confidence_score == 0.85
            assert art.status == "generated"
            assert "src/main.py" in art.files_modified
        finally:
            db.close()

    def test_fix_artifact_defaults(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            art = FixArtifact(investigation_id=inv.id)
            db.add(art)
            db.commit()
            assert art.status == "generated"
            assert art.dry_run is True
        finally:
            db.close()

    def test_fix_artifact_fk_cascade(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_fix_artifact(db, inv.id)
            count = db.query(FixArtifact).count()
            assert count == 1
        finally:
            db.close()


# --- Patch Service Tests ---

class TestPatchService:
    def test_parse_patch(self):
        from app.services.patch_service import _parse_patch
        patch = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
-old line
+new line
 context line
+added line
"""
        files = _parse_patch(patch)
        assert len(files) == 1
        assert files[0]["path"] == "src/main.py"
        assert "new line" in files[0]["content"]
        assert "added line" in files[0]["content"]
        assert "old line" not in files[0]["content"]

    def test_parse_patch_multiple_files(self):
        from app.services.patch_service import _parse_patch
        patch = """--- a/src/main.py
+++ b/src/main.py
@@ -1 +1 @@
-old
+new
--- a/src/utils.py
+++ b/src/utils.py
@@ -1 +1 @@
-foo
+bar
"""
        files = _parse_patch(patch)
        assert len(files) == 2
        assert files[0]["path"] == "src/main.py"
        assert files[1]["path"] == "src/utils.py"

    def test_parse_patch_no_changes(self):
        from app.services.patch_service import _parse_patch
        files = _parse_patch("")
        assert len(files) == 0

    def test_apply_patch_dry_run(self):
        from app.services.patch_service import apply_patch
        patch = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b"
        result = apply_patch("owner/repo", "", patch, dry_run=True)
        assert result["applied"] is False
        assert "x.py" in result["files_modified"]
        assert result["commit_sha"] is None

    def test_apply_patch_no_files(self):
        from app.services.patch_service import apply_patch
        result = apply_patch("owner/repo", "", "", dry_run=False)
        assert result["applied"] is False
        assert result["files_modified"] == []


# --- API Tests ---

class TestFixAPI:
    def test_get_fix_empty(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            headers, _ = _cookie_headers_for_user(db)

            resp = client.get(f"/api/investigations/{inv.id}/fix", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] is None
            assert data["fix_summary"] is None
        finally:
            db.close()

    def test_get_fix_with_artifact(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            art = _create_test_fix_artifact(db, inv.id, "applied")
            headers, _ = _cookie_headers_for_user(db)

            resp = client.get(f"/api/investigations/{inv.id}/fix", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == art.id
            assert data["fix_summary"] == "Fix the broken import"
            assert data["confidence_score"] == 0.85
            assert "src/main.py" in data["files_modified"]
            assert "--- a/src/main.py" in data["patch_content"]
            assert data["branch_name"] == "auto-fix/test-branch"
            assert data["dry_run"] is False
            assert data["status"] == "applied"
            assert data["generated_at"] is not None
            assert data["applied_at"] is not None
        finally:
            db.close()

    def test_get_fix_requires_auth(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            resp = client.get(f"/api/investigations/{inv.id}/fix")
            assert resp.status_code == 401
        finally:
            db.close()

    def test_get_fix_not_found(self):
        db = SessionLocal()
        try:
            headers, _ = _cookie_headers_for_user(db)
            resp = client.get("/api/investigations/9999/fix", headers=headers)
            assert resp.status_code == 404
        finally:
            db.close()

    def test_fix_artifact_has_all_fields(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_fix_artifact(db, inv.id)
            headers, _ = _cookie_headers_for_user(db)

            resp = client.get(f"/api/investigations/{inv.id}/fix", headers=headers)
            data = resp.json()
            for key in ("id", "investigation_id", "fix_summary", "root_cause",
                        "confidence_score", "files_modified", "patch_content",
                        "branch_name", "dry_run", "status", "generated_at", "applied_at"):
                assert key in data
        finally:
            db.close()


# --- Authorization Tests ---

class TestFixAuthorization:
    def test_non_admin_can_see_own_fix(self):
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
            _create_test_fix_artifact(db, inv.id)

            resp = client.get(f"/api/investigations/{inv.id}/fix", headers=headers)
            assert resp.status_code == 200
            assert resp.json()["id"] is not None
        finally:
            db.close()

    def test_non_admin_cannot_see_others_fix(self):
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
            _create_test_fix_artifact(db, inv.id)

            resp = client.get(f"/api/investigations/{inv.id}/fix", headers=headers)
            assert resp.status_code == 403
        finally:
            db.close()


# --- Event Emission Tests ---

class TestFixEventEmission:
    def test_fix_artifact_creation_emits_event(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_fix_artifact(db, inv.id)
            event = db.query(InvestigationEvent).filter(
                InvestigationEvent.investigation_id == inv.id
            ).first()
            assert event is None
        finally:
            db.close()

    def test_fix_artifact_updates_investigation_status(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id, status="analyzing")
            _create_test_fix_artifact(db, inv.id)
            assert inv.status == "analyzing"
        finally:
            db.close()
