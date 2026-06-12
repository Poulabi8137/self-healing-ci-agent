"""Analytics service — real database-backed operational metrics.

All 8 metrics computed from existing tables only:
  failures, investigations, validation_results, fix_artifacts,
  pr_records, repositories, investigation_events.

No synthetic data, no demo calculations.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, cast, Date

from app.database.db import SessionLocal
from app.database.models import (
    Failure, Investigation, ValidationResult, FixArtifact,
    PRRecord, Repository, InvestigationEvent,
)
from app.utils.cache import ttl_cache
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date_ranges(
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[datetime | None, datetime | None]:
    """Return (start_dt, end_dt) from days or explicit date strings."""
    if days:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        return start, end
    if start_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
        return start, end
    return None, None


def _apply_repo_filter(query, model_col, repo_ids: list[int] | None):
    if repo_ids:
        return query.filter(model_col.in_(repo_ids))
    return query


# ---------------------------------------------------------------------------
# 1. MTTR — Mean Time To Resolution
# ---------------------------------------------------------------------------

def compute_mttr(repo_ids: list[int] | None = None, days: int | None = None) -> dict[str, Any]:
    """Global and per-repo MTTR in seconds and human-readable format."""
    start, end = _parse_date_ranges(days)
    db = SessionLocal()
    try:
        q = db.query(
            Investigation.id, Investigation.repository_id,
            Investigation.created_at, Investigation.completed_at,
            Investigation.status,
        ).filter(
            Investigation.status == "completed",
            Investigation.completed_at.isnot(None),
            Investigation.created_at.isnot(None),
        )
        if start:
            q = q.filter(Investigation.created_at >= start)
        if end:
            q = q.filter(Investigation.created_at <= end)
        q = _apply_repo_filter(q, Investigation.repository_id, repo_ids)
        rows = q.all()

        durations = []
        repo_durations: dict[int, list[float]] = {}
        for row in rows:
            secs = (row.completed_at - row.created_at).total_seconds()
            durations.append(secs)
            repo_durations.setdefault(row.repository_id, []).append(secs)

        global_mttr_secs = sum(durations) / len(durations) if durations else 0.0
        global_mttr_str = _format_duration(global_mttr_secs)

        per_repo = {}
        repo_names = _repo_names(db)
        for rid, dur_list in repo_durations.items():
            avg = sum(dur_list) / len(dur_list)
            per_repo[repo_names.get(rid, f"repo-{rid}")] = {
                "seconds": round(avg, 1),
                "formatted": _format_duration(avg),
                "investigations_count": len(dur_list),
            }

        return {
            "global_mttr_seconds": round(global_mttr_secs, 1),
            "global_mttr_formatted": global_mttr_str,
            "total_resolved": len(durations),
            "per_repository": per_repo,
        }
    finally:
        db.close()


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


# ---------------------------------------------------------------------------
# 2. Success Rate
# ---------------------------------------------------------------------------

def compute_success_rate(repo_ids: list[int] | None = None, days: int | None = None) -> dict[str, Any]:
    """Successful investigations / total investigations."""
    start, end = _parse_date_ranges(days)
    db = SessionLocal()
    try:
        q = db.query(Investigation.id, Investigation.status, Investigation.repository_id)
        if start:
            q = q.filter(Investigation.created_at >= start)
        if end:
            q = q.filter(Investigation.created_at <= end)
        q = _apply_repo_filter(q, Investigation.repository_id, repo_ids)
        rows = q.all()

        total = len(rows)
        successful = sum(1 for r in rows if r.status == "completed")
        rate = round(successful / total * 100, 1) if total else 0.0

        # Per repo
        repo_data: dict[int, dict] = {}
        for r in rows:
            rd = repo_data.setdefault(r.repository_id, {"total": 0, "successful": 0})
            rd["total"] += 1
            if r.status == "completed":
                rd["successful"] += 1

        repo_names = _repo_names(db)
        per_repo = {}
        for rid, rd in repo_data.items():
            per_repo[repo_names.get(rid, f"repo-{rid}")] = {
                "rate": round(rd["successful"] / rd["total"] * 100, 1) if rd["total"] else 0.0,
                "total": rd["total"],
                "successful": rd["successful"],
            }

        return {
            "global_success_rate": rate,
            "total_investigations": total,
            "successful_investigations": successful,
            "per_repository": per_repo,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Failure Rate
# ---------------------------------------------------------------------------

def compute_failure_rate(repo_ids: list[int] | None = None, days: int | None = None) -> dict[str, Any]:
    """Failures / total workflow executions."""
    start, end = _parse_date_ranges(days)
    db = SessionLocal()
    try:
        # Count failures
        fq = db.query(Failure.id, Failure.repository_id)
        if start:
            fq = fq.filter(Failure.detected_at >= start)
        if end:
            fq = fq.filter(Failure.detected_at <= end)
        fq = _apply_repo_filter(fq, Failure.repository_id, repo_ids)
        failures = fq.all()

        # Count completed / failed investigations as "workflow executions"
        iq = db.query(Investigation.id, Investigation.repository_id)
        if start:
            iq = iq.filter(Investigation.created_at >= start)
        if end:
            iq = iq.filter(Investigation.created_at <= end)
        iq = _apply_repo_filter(iq, Investigation.repository_id, repo_ids)
        investigations = iq.all()

        total_executions = len(failures) + len(investigations) or 1
        rate = round(len(failures) / total_executions * 100, 1)

        repo_names = _repo_names(db)
        per_repo = _count_repo_items(failures, repo_names, "failures")

        return {
            "global_failure_rate": rate,
            "total_failures": len(failures),
            "total_executions": total_executions,
            "per_repository": per_repo,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. Auto-Heal Rate
# ---------------------------------------------------------------------------

def compute_auto_heal_rate(repo_ids: list[int] | None = None, days: int | None = None) -> dict[str, Any]:
    """PRs created (from pr_created events) / failures detected."""
    start, end = _parse_date_ranges(days)
    db = SessionLocal()
    try:
        fq = db.query(Failure.id, Failure.repository_id)
        if start:
            fq = fq.filter(Failure.detected_at >= start)
        if end:
            fq = fq.filter(Failure.detected_at <= end)
        fq = _apply_repo_filter(fq, Failure.repository_id, repo_ids)
        failures = fq.all()

        # Count pr_created events
        eq = db.query(InvestigationEvent.id).filter(
            InvestigationEvent.event_type == "pr_created"
        )
        if start:
            eq = eq.filter(InvestigationEvent.created_at >= start)
        if end:
            eq = eq.filter(InvestigationEvent.created_at <= end)
        pr_events = eq.count()

        total_failures = len(failures) or 1
        rate = round(pr_events / total_failures * 100, 1)

        return {
            "global_auto_heal_rate": rate,
            "prs_created": pr_events,
            "failures_detected": total_failures - 1 + len(failures),  # correct off-by-one from `or 1`
            "per_repository": {},
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 5. Validation Accuracy
# ---------------------------------------------------------------------------

def compute_validation_accuracy(repo_ids: list[int] | None = None, days: int | None = None) -> dict[str, Any]:
    """Validations passed / validations executed, overall and per type."""
    start, end = _parse_date_ranges(days)
    db = SessionLocal()
    try:
        q = db.query(ValidationResult.validation_type, ValidationResult.status, ValidationResult.investigation_id)
        if start:
            q = q.filter(ValidationResult.created_at >= start)
        if end:
            q = q.filter(ValidationResult.created_at <= end)
        if repo_ids:
            q = q.join(Investigation).filter(Investigation.repository_id.in_(repo_ids))
        rows = q.all()

        total = len(rows)
        passed = sum(1 for r in rows if r.status == "passed")
        overall_rate = round(passed / total * 100, 1) if total else 0.0

        type_counts: dict[str, dict] = {}
        for r in rows:
            tc = type_counts.setdefault(r.validation_type, {"total": 0, "passed": 0})
            tc["total"] += 1
            if r.status == "passed":
                tc["passed"] += 1

        per_type = {}
        for t, tc in type_counts.items():
            per_type[t] = {
                "accuracy": round(tc["passed"] / tc["total"] * 100, 1) if tc["total"] else 0.0,
                "total": tc["total"],
                "passed": tc["passed"],
            }

        return {
            "overall_accuracy": overall_rate,
            "total_validations": total,
            "passed_validations": passed,
            "per_type": per_type,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 6. PR Acceptance Rate
# ---------------------------------------------------------------------------

def compute_pr_acceptance_rate(repo_ids: list[int] | None = None) -> dict[str, Any]:
    """Merged PRs / created PRs."""
    db = SessionLocal()
    try:
        q = db.query(PRRecord.status, PRRecord.repository_id)
        q = _apply_repo_filter(q, PRRecord.repository_id, repo_ids)
        rows = q.all()

        total = len(rows)
        merged = sum(1 for r in rows if r.status == "merged")
        rate = round(merged / total * 100, 1) if total else 0.0

        return {
            "global_pr_acceptance_rate": rate,
            "total_prs": total,
            "merged_prs": merged,
            "per_repository": {},
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 7. Repository Health Score
# ---------------------------------------------------------------------------

HEALTH_SCORE_WEIGHTS = {
    "failure_penalty": -15,           # per recent failure
    "validation_bonus": 10,           # per passed validation
    "healed_bonus": 20,               # per auto-healed investigation
    "unresolved_penalty": -10,        # per unresolved investigation
    "health_score_max": 100,
    "health_score_min": 0,
}


def compute_repository_health_scores(repo_ids: list[int] | None = None) -> dict[str, Any]:
    """Deterministic health scoring model.

    Formula:
      base_score = 50
      + (passed_validations * validation_bonus)
      + (auto_healed_count * healed_bonus)
      + (recent_failures * failure_penalty)
      + (unresolved_investigations * unresolved_penalty)
      clamped to [0, 100]
    """
    db = SessionLocal()
    try:
        repos = db.query(Repository).all()
        if repo_ids:
            repos = [r for r in repos if r.id in repo_ids]

        repo_names = _repo_names(db)
        scores = {}
        for repo in repos:
            recent_failures = db.query(Failure).filter(
                Failure.repository_id == repo.id,
            ).count()

            passed_validations = db.query(ValidationResult).join(
                Investigation, ValidationResult.investigation_id == Investigation.id
            ).filter(
                Investigation.repository_id == repo.id,
                ValidationResult.status == "passed",
            ).count()

            healed = db.query(Investigation).filter(
                Investigation.repository_id == repo.id,
                Investigation.status == "completed",
                Investigation.root_cause.isnot(None),
            ).count()

            unresolved = db.query(Investigation).filter(
                Investigation.repository_id == repo.id,
                Investigation.status.in_(["detecting", "analyzing", "fixing", "validating"]),
            ).count()

            base = 50
            raw = (base
                   + passed_validations * HEALTH_SCORE_WEIGHTS["validation_bonus"]
                   + healed * HEALTH_SCORE_WEIGHTS["healed_bonus"]
                   + recent_failures * HEALTH_SCORE_WEIGHTS["failure_penalty"]
                   + unresolved * HEALTH_SCORE_WEIGHTS["unresolved_penalty"])
            score = max(HEALTH_SCORE_WEIGHTS["health_score_min"],
                        min(HEALTH_SCORE_WEIGHTS["health_score_max"], raw))

            scores[repo_names.get(repo.id, repo.full_name)] = {
                "score": score,
                "recent_failures": recent_failures,
                "passed_validations": passed_validations,
                "auto_healed": healed,
                "unresolved_investigations": unresolved,
            }

        return {
            "formula": "base=50 + val_bonus*10 + healed*20 - failures*15 - unresolved*10, clamped [0,100]",
            "per_repository": scores,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 8. Failure Categories
# ---------------------------------------------------------------------------

def compute_failure_categories(repo_ids: list[int] | None = None, days: int | None = None) -> dict[str, Any]:
    """Aggregate failures by error_category from investigations."""
    start, end = _parse_date_ranges(days)
    db = SessionLocal()
    try:
        q = db.query(Investigation.error_category, func.count(Investigation.id))
        q = q.filter(Investigation.error_category.isnot(None))
        if start:
            q = q.filter(Investigation.created_at >= start)
        if end:
            q = q.filter(Investigation.created_at <= end)
        q = _apply_repo_filter(q, Investigation.repository_id, repo_ids)
        q = q.group_by(Investigation.error_category)
        rows = q.all()

        categories = {cat: count for cat, count in rows}
        total = sum(categories.values()) or 1

        # Ensure all standard categories are present
        for std_cat in ["syntax", "dependency", "configuration", "test", "infrastructure", "unknown"]:
            categories.setdefault(std_cat, 0)

        return {
            "categories": categories,
            "total": sum(categories.values()),
            "breakdown": {
                cat: {
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for cat, count in categories.items()
            },
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Aggregated overview
# ---------------------------------------------------------------------------

@ttl_cache(ttl_seconds=30)
def compute_analytics_overview(
    repo_ids: list[int] | None = None,
    days: int | None = None,
) -> dict[str, Any]:
    """Compute all analytics and return a single overview dict."""
    mttr = compute_mttr(repo_ids, days)
    success = compute_success_rate(repo_ids, days)
    failure = compute_failure_rate(repo_ids, days)
    auto_heal = compute_auto_heal_rate(repo_ids, days)
    validation = compute_validation_accuracy(repo_ids, days)
    pr_rate = compute_pr_acceptance_rate(repo_ids)
    health = compute_repository_health_scores(repo_ids)
    categories = compute_failure_categories(repo_ids, days)

    return {
        "mttr": mttr,
        "success_rate": success,
        "failure_rate": failure,
        "auto_heal_rate": auto_heal,
        "validation_accuracy": validation,
        "pr_acceptance_rate": pr_rate,
        "repository_health": health,
        "failure_categories": categories,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _repo_names(db) -> dict[int, str]:
    return {r.id: r.full_name for r in db.query(Repository).all()}


def _count_repo_items(rows, name_map: dict[int, str], label: str) -> dict:
    counts: dict[int, int] = {}
    for r in rows:
        counts[r.repository_id] = counts.get(r.repository_id, 0) + 1
    result = {}
    for rid, count in counts.items():
        result[name_map.get(rid, f"repo-{rid}")] = {label: count}
    return result
