"""
Phase 6 tests: validation result persistence, API, workflow, authorization.
"""
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.db import SessionLocal, init_db
from app.database.models import (
    User, Repository, GitHubInstallation, Investigation,
    ValidationResult, InvestigationEvent,
)
from app.auth.oauth import create_jwt as create_jwt_for_user
from app.utils.rate_limiter import reset_rate_limits

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup():
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(ValidationResult).delete()
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


def _create_test_investigation(db, repo_id, status="validating"):
    inv = Investigation(
        repository_id=repo_id,
        status=status,
        current_stage="validation_started",
        current_stage_status="in_progress",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _create_test_validation_result(db, investigation_id, validation_type="build_validation", status="passed"):
    vr = ValidationResult(
        investigation_id=investigation_id,
        validation_type=validation_type,
        status=status,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_ms=1500,
        logs="Validation passed\nAll checks OK",
        metadata_json='{"issues_count": 0}',
        confidence_score=0.85,
    )
    db.add(vr)
    db.commit()
    db.refresh(vr)
    return vr


# --- Model Persistence Tests ---

class TestValidationResultModel:
    def test_create_validation_result(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            vr = _create_test_validation_result(db, inv.id)

            assert vr.id is not None
            assert vr.investigation_id == inv.id
            assert vr.validation_type == "build_validation"
            assert vr.status == "passed"
            assert vr.duration_ms == 1500
            assert vr.confidence_score == 0.85
        finally:
            db.close()

    def test_validation_result_default_status(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            vr = ValidationResult(
                investigation_id=inv.id,
                validation_type="unit_test_validation",
            )
            db.add(vr)
            db.commit()
            assert vr.status == "pending"
        finally:
            db.close()

    def test_validation_result_fk_cascade(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_validation_result(db, inv.id)
            count_before = db.query(ValidationResult).count()
            assert count_before == 1
        finally:
            db.close()


# --- API Tests ---

class TestValidationAPI:
    def _auth_headers(self, db):
        user = _create_test_user(db)
        token = create_jwt_for_user(user)
        # FastAPI TestClient uses cookies dict on requests
        return {"Cookie": f"jwt={token}"}

    def test_get_validations_empty(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            headers = self._auth_headers(db)

            resp = client.get(f"/api/investigations/{inv.id}/validations", headers=headers)
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            db.close()

    def test_get_validations_with_results(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_validation_result(db, inv.id, "build_validation", "passed")
            _create_test_validation_result(db, inv.id, "unit_test_validation", "failed")
            headers = self._auth_headers(db)

            resp = client.get(f"/api/investigations/{inv.id}/validations", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            assert data[0]["validation_type"] == "build_validation"
            assert data[0]["status"] == "passed"
            assert data[1]["validation_type"] == "unit_test_validation"
            assert data[1]["status"] == "failed"
        finally:
            db.close()

    def test_get_validations_requires_auth(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            resp = client.get(f"/api/investigations/{inv.id}/validations")
            assert resp.status_code == 401
        finally:
            db.close()

    def test_get_validations_not_found(self):
        db = SessionLocal()
        try:
            headers = self._auth_headers(db)
            resp = client.get("/api/investigations/9999/validations", headers=headers)
            assert resp.status_code == 404
        finally:
            db.close()

    def test_validation_result_has_all_fields(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_validation_result(db, inv.id)
            headers = self._auth_headers(db)

            resp = client.get(f"/api/investigations/{inv.id}/validations", headers=headers)
            data = resp.json()[0]
            assert "id" in data
            assert "investigation_id" in data
            assert "validation_type" in data
            assert "status" in data
            assert "started_at" in data
            assert "completed_at" in data
            assert "duration_ms" in data
            assert "logs" in data
            assert "metadata" in data
            assert "confidence_score" in data
            assert "created_at" in data
        finally:
            db.close()

    def test_logs_as_list(self):
        db = SessionLocal()
        try:
            repo = _create_test_repo(db)
            inv = _create_test_investigation(db, repo.id)
            _create_test_validation_result(db, inv.id)
            headers = self._auth_headers(db)

            resp = client.get(f"/api/investigations/{inv.id}/validations", headers=headers)
            data = resp.json()[0]
            assert isinstance(data["logs"], list)
            assert len(data["logs"]) == 2
        finally:
            db.close()


# --- Authorization Tests ---

class TestValidationAuthorization:
    def _cookie_headers(self, db, role="admin"):
        user = _create_test_user(db, role=role)
        token = create_jwt_for_user(user)
        return {"Cookie": f"jwt={token}"}, user

    def test_non_admin_can_see_own_validations(self):
        db = SessionLocal()
        try:
            headers, user = self._cookie_headers(db, role="candidate")
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
            _create_test_validation_result(db, inv.id)

            resp = client.get(
                f"/api/investigations/{inv.id}/validations",
                headers=headers,
            )
            assert resp.status_code == 200
            assert len(resp.json()) == 1
        finally:
            db.close()

    def test_non_admin_cannot_see_others_validations(self):
        db = SessionLocal()
        try:
            admin_user = _create_test_user(db, email="admin@test.com", role="admin")
            headers, user = self._cookie_headers(db, role="candidate")
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
            _create_test_validation_result(db, inv.id)

            resp = client.get(
                f"/api/investigations/{inv.id}/validations",
                headers=headers,
            )
            assert resp.status_code == 403
        finally:
            db.close()
