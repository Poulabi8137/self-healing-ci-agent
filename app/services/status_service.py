"""Repository health status derivation — computed at query time, no dedicated table."""
from app.database.models import Repository, Investigation, InvestigationEvent


def derive_repository_status(repo: Repository, db) -> str:
    """Derive human-readable health status from existing DB state.

    Status is computed on-the-fly — no table needed.
    """
    if not repo.is_active:
        return "disabled"

    active = db.query(Investigation).filter(
        Investigation.repository_id == repo.id,
        Investigation.status.in_(["detecting", "analyzing"]),
    ).first()
    if active:
        return "investigating"

    fixing = db.query(Investigation).filter(
        Investigation.repository_id == repo.id,
        Investigation.status.in_(["fixing", "fix_proposed"]),
    ).first()
    if fixing:
        return "fixing"

    validating = db.query(Investigation).filter(
        Investigation.repository_id == repo.id,
        Investigation.status == "validating",
    ).first()
    if validating:
        return "validating"

    pr_created = db.query(InvestigationEvent).join(
        Investigation, InvestigationEvent.investigation_id == Investigation.id
    ).filter(
        Investigation.repository_id == repo.id,
        InvestigationEvent.event_type == "pr_created",
    ).first()
    if pr_created:
        return "pr_created"

    failed = db.query(Investigation).filter(
        Investigation.repository_id == repo.id,
        Investigation.status == "failed",
    ).first()
    if failed:
        return "failed"

    completed = db.query(Investigation).filter(
        Investigation.repository_id == repo.id,
        Investigation.status == "completed",
    ).order_by(Investigation.completed_at.desc()).first()
    if completed:
        return "completed"

    if repo.last_workflow_status == "failure":
        return "failed"

    return "active"
