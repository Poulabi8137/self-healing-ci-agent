import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request

from app.auth.dependencies import get_current_jwt_user
from app.database.db import SessionLocal
from app.database.models import Investigation, InvestigationEvent, ValidationResult, FixArtifact, PRRecord, User, Repository, GitHubInstallation
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/investigations")


def _investigation_to_dict(inv: Investigation) -> dict:
    stages_raw = inv.stages
    if isinstance(stages_raw, str):
        try:
            stages = json.loads(stages_raw)
        except (json.JSONDecodeError, TypeError):
            stages = []
    else:
        stages = stages_raw or []
    return {
        "id": inv.id,
        "failure_id": inv.failure_id,
        "repository_id": inv.repository_id,
        "status": inv.status,
        "root_cause": inv.root_cause,
        "error_category": inv.error_category,
        "confidence": inv.confidence,
        "summary": inv.summary,
        "stages": stages,
        "current_stage": inv.current_stage,
        "current_stage_status": inv.current_stage_status,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
    }


@router.get("/")
async def list_investigations(
    request: Request,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
):
    user: User = await get_current_jwt_user(request)
    db = SessionLocal()
    try:
        query = db.query(Investigation).order_by(Investigation.created_at.desc())

        if status:
            query = query.filter(Investigation.status == status)

        if user.role != "admin":
            installations = db.query(GitHubInstallation).filter(
                GitHubInstallation.user_id == user.id
            ).all()
            inst_ids = [i.id for i in installations]
            repos = db.query(Repository).filter(
                Repository.github_installation_id.in_(inst_ids)
            ).all() if inst_ids else []
            repo_ids = [r.id for r in repos]
            query = query.filter(
                Investigation.repository_id.in_(repo_ids)
            ) if repo_ids else query.filter(False)

        investigations = query.limit(limit).all()
        return [_investigation_to_dict(inv) for inv in investigations]
    finally:
        db.close()


@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: int,
    request: Request,
):
    user: User = await get_current_jwt_user(request)
    db = SessionLocal()
    try:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")

        if user.role != "admin":
            installations = db.query(GitHubInstallation).filter(
                GitHubInstallation.user_id == user.id
            ).all()
            inst_ids = [i.id for i in installations]
            repos = db.query(Repository).filter(
                Repository.github_installation_id.in_(inst_ids)
            ).all() if inst_ids else []
            repo_ids = [r.id for r in repos]
            if inv.repository_id not in repo_ids:
                raise HTTPException(status_code=403, detail="Access denied")

        return _investigation_to_dict(inv)
    finally:
        db.close()


@router.get("/{investigation_id}/validations")
async def get_investigation_validations(
    investigation_id: int,
    request: Request,
):
    """Return all persisted validation results for an investigation, ordered by creation time."""
    user: User = await get_current_jwt_user(request)
    db = SessionLocal()
    try:
        from app.database.models import Investigation, Repository, GitHubInstallation

        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")

        if user.role != "admin":
            installations = db.query(GitHubInstallation).filter(
                GitHubInstallation.user_id == user.id
            ).all()
            inst_ids = [i.id for i in installations]
            repos = db.query(Repository).filter(
                Repository.github_installation_id.in_(inst_ids)
            ).all() if inst_ids else []
            repo_ids = [r.id for r in repos]
            if inv.repository_id not in repo_ids:
                raise HTTPException(status_code=403, detail="Access denied")

        results = (
            db.query(ValidationResult)
            .filter(ValidationResult.investigation_id == investigation_id)
            .order_by(ValidationResult.created_at.asc())
            .all()
        )

        return [
            {
                "id": r.id,
                "investigation_id": r.investigation_id,
                "validation_type": r.validation_type,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_ms": r.duration_ms,
                "logs": r.logs.split("\n") if r.logs else [],
                "metadata": json.loads(r.metadata_json) if r.metadata_json else {},
                "confidence_score": r.confidence_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]
    finally:
        db.close()


@router.get("/{investigation_id}/fix")
async def get_investigation_fix(
    investigation_id: int,
    request: Request,
):
    """Return the persisted fix artifact for an investigation."""
    user: User = await get_current_jwt_user(request)
    db = SessionLocal()
    try:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")

        if user.role != "admin":
            installations = db.query(GitHubInstallation).filter(
                GitHubInstallation.user_id == user.id
            ).all()
            inst_ids = [i.id for i in installations]
            repos = db.query(Repository).filter(
                Repository.github_installation_id.in_(inst_ids)
            ).all() if inst_ids else []
            repo_ids = [r.id for r in repos]
            if inv.repository_id not in repo_ids:
                raise HTTPException(status_code=403, detail="Access denied")

        artifact = (
            db.query(FixArtifact)
            .filter(FixArtifact.investigation_id == investigation_id)
            .order_by(FixArtifact.generated_at.desc())
            .first()
        )

        if not artifact:
            return {
                "id": None,
                "investigation_id": investigation_id,
                "fix_summary": None,
                "root_cause": None,
                "confidence_score": None,
                "files_modified": [],
                "patch_content": None,
                "branch_name": None,
                "dry_run": True,
                "status": None,
                "generated_at": None,
                "applied_at": None,
            }

        return {
            "id": artifact.id,
            "investigation_id": artifact.investigation_id,
            "fix_summary": artifact.fix_summary,
            "root_cause": artifact.root_cause,
            "confidence_score": artifact.confidence_score,
            "files_modified": json.loads(artifact.files_modified) if artifact.files_modified else [],
            "patch_content": artifact.patch_content,
            "branch_name": artifact.branch_name,
            "dry_run": artifact.dry_run,
            "status": artifact.status,
            "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None,
            "applied_at": artifact.applied_at.isoformat() if artifact.applied_at else None,
        }
    finally:
        db.close()


@router.get("/{investigation_id}/pull-request")
async def get_investigation_pull_request(
    investigation_id: int,
    request: Request,
):
    """Return the persisted pull request record for an investigation."""
    user: User = await get_current_jwt_user(request)
    db = SessionLocal()
    try:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")

        if user.role != "admin":
            installations = db.query(GitHubInstallation).filter(
                GitHubInstallation.user_id == user.id
            ).all()
            inst_ids = [i.id for i in installations]
            repos = db.query(Repository).filter(
                Repository.github_installation_id.in_(inst_ids)
            ).all() if inst_ids else []
            repo_ids = [r.id for r in repos]
            if inv.repository_id not in repo_ids:
                raise HTTPException(status_code=403, detail="Access denied")

        record = (
            db.query(PRRecord)
            .filter(PRRecord.investigation_id == investigation_id)
            .order_by(PRRecord.created_at.desc())
            .first()
        )

        if not record:
            return {
                "id": None,
                "investigation_id": investigation_id,
                "pr_number": None,
                "pr_url": None,
                "title": None,
                "description": None,
                "branch_name": None,
                "status": None,
                "dry_run": True,
                "created_at": None,
            }

        return {
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
    finally:
        db.close()
