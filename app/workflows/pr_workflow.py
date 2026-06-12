"""PR creation workflow — consume fix artifact + validation, create PR, persist."""
import json
from datetime import datetime, timezone
from typing import Any

from app.utils.logger import get_logger
from app.database.db import SessionLocal
from app.database.models import Investigation, FixArtifact, ValidationResult, PRRecord, Repository, GitHubInstallation
from app.services.event_manager import event_manager
from app.services.pr_service import (
    create_pull_request_async,
    generate_pr_title,
    generate_pr_description,
)
from app.services.github_app import get_installation_token

logger = get_logger(__name__)


async def run_pr_workflow(
    repository_name: str,
    logs: str,
    dry_run: bool = True,
    approved: bool = False,
    investigation_id: int | None = None,
) -> dict[str, Any]:
    """End-to-end PR creation pipeline.

    Pipeline:
    1. Load fix artifact and validation results for the investigation.
    2. Generate PR title and description.
    3. Create PR on GitHub (if not dry_run and approved).
    4. Persist PR record.
    5. Update investigation status.
    6. Emit pr_created event.

    Args:
        repository_name: Repository identifier.
        logs: Raw CI/CD workflow logs (passed through for compatibility).
        dry_run: If True, only simulate PR creation (default True).
        approved: If False, PR creation is blocked (default False).
        investigation_id: Investigation ID for event linking.

    Returns:
        Dict with PR creation result.
    """
    logger.info(f"Starting PR workflow for '{repository_name}' (dry_run={dry_run}, approved={approved})")

    pr_title = "[Auto-Heal] Automated fix"
    pr_description = ""
    branch_name = None
    pr_number = None
    pr_url = None
    modified_files: list[str] = []
    fix_summary = ""
    root_cause = ""
    confidence_score = 0.0
    validation_stages: list[dict] = []

    # 1. Load fix artifact and validation data
    if investigation_id:
        db = SessionLocal()
        try:
            artifact = db.query(FixArtifact).filter(
                FixArtifact.investigation_id == investigation_id
            ).order_by(FixArtifact.generated_at.desc()).first()

            if artifact:
                fix_summary = artifact.fix_summary or ""
                root_cause = artifact.root_cause or ""
                confidence_score = artifact.confidence_score or 0.0
                branch_name = artifact.branch_name
                modified_files = json.loads(artifact.files_modified) if artifact.files_modified else []

            validation_results = db.query(ValidationResult).filter(
                ValidationResult.investigation_id == investigation_id
            ).order_by(ValidationResult.created_at.asc()).all()

            validation_stages = [
                {
                    "stage": r.validation_type,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                }
                for r in validation_results
            ]
        finally:
            db.close()

    # 2. Generate PR content
    pr_title = generate_pr_title(fix_summary)
    pr_description = generate_pr_description(
        fix_summary=fix_summary,
        root_cause=root_cause,
        modified_files=modified_files,
        validation_stages=validation_stages,
        confidence_score=confidence_score,
    )

    # 3. Create PR on GitHub (non dry_run + approved)
    pr_number = None
    pr_url = None
    base_branch = "main"

    if not dry_run and approved and investigation_id:
        installation_token = None
        db = SessionLocal()
        try:
            inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
            if inv and inv.repository_id:
                repo = db.query(Repository).filter(Repository.id == inv.repository_id).first()
                if repo:
                    base_branch = repo.default_branch or "main"
                    if repo.github_installation_id:
                        install = db.query(GitHubInstallation).filter(
                            GitHubInstallation.id == repo.github_installation_id
                        ).first()
                        if install:
                            try:
                                installation_token = get_installation_token(install.installation_id)
                            except Exception as e:
                                logger.warning(f"Failed to get installation token: {e}")

            if installation_token and branch_name:
                pr_result = await create_pull_request_async(
                    repo_full_name=repository_name,
                    installation_token=installation_token,
                    title=pr_title,
                    body=pr_description,
                    head=branch_name,
                    base=base_branch,
                )
                pr_number = pr_result.get("number")
                pr_url = pr_result.get("html_url")
        finally:
            db.close()

    # 4. Determine status
    if not approved:
        status = "blocked"
    elif dry_run:
        status = "simulated"
    elif pr_number:
        status = "created"
    else:
        status = "failed"

    # 5. Persist PR record
    db = SessionLocal()
    try:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first() if investigation_id else None
        repo_id = inv.repository_id if inv else None

        record = PRRecord(
            investigation_id=investigation_id,
            repository_id=repo_id,
            repository_name=repository_name,
            branch_name=branch_name or "",
            pr_title=pr_title,
            pr_number=pr_number,
            pr_url=pr_url,
            description=pr_description,
            status=status,
            dry_run=dry_run,
        )
        db.add(record)
        db.commit()

        # Update investigation status
        if inv:
            inv.status = "completed"
            inv.current_stage = "pr_created"
            inv.current_stage_status = "completed"
            inv.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

    # 6. Emit pr_created event
    if investigation_id:
        try:
            await event_manager.publish(
                event_type="pr_created",
                data={
                    "repository": repository_name,
                    "pr_number": pr_number,
                    "pr_url": pr_url,
                    "pr_title": pr_title,
                    "branch_name": branch_name,
                    "files_modified": modified_files,
                    "status": status,
                },
                investigation_id=investigation_id,
            )
        except Exception as e:
            logger.warning(f"Failed to publish pr_created event: {e}")

    result: dict[str, Any] = {
        "status": status,
        "dry_run": dry_run,
        "approved": approved,
        "pr_title": pr_title,
        "pr_description": pr_description,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "branch_name": branch_name,
        "files_modified": modified_files,
        "validation_stages": validation_stages,
    }

    logger.info(f"PR workflow complete for '{repository_name}' — status: {status}")
    return result
