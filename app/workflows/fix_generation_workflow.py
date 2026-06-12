import json
from datetime import datetime, timezone
from typing import Any, Dict

from app.utils.logger import get_logger
from app.workflows.analysis_workflow import run_analysis
from app.agents.fix_agent import FixAgent
from app.services.event_manager import event_manager
from app.services.patch_service import apply_patch_async
from app.database.db import SessionLocal
from app.database.models import Investigation, FixArtifact

logger = get_logger(__name__)


async def run_fix_generation(
    repository_name: str,
    logs: str,
    investigation_id: int | None = None,
) -> Dict[str, Any]:
    """End-to-end fix generation workflow: analyze → retrieve → generate fix.

    Pipeline:
    1. Run root cause analysis (parse → classify → retrieve → reason)
    2. Generate fix proposal using analysis results + repository context

    Args:
        repository_name: Name of the repository (must match an indexed vector store).
        logs: Raw CI/CD workflow logs.

    Returns:
        Structured fix proposal dict.
    """
    logger.info(f"Starting fix generation workflow for '{repository_name}'")

    # 1. Run analysis workflow
    analysis = await run_analysis(
        repository_name=repository_name,
        logs=logs,
        investigation_id=investigation_id,
    )

    # 2. Generate fix proposal
    agent = FixAgent()
    fix_proposal = await agent.generate_fix(
        root_cause_analysis=analysis["root_cause"],
        analysis_summary=analysis["analysis_summary"],
        error_category=analysis["error_category"],
        failure_type=analysis.get("raw_failure_type", "unknown"),
        logs=logs,
        repository_name=repository_name,
        affected_files=analysis.get("affected_files", []),
        confidence=analysis["confidence"],
        top_k=5,
    )

    # 3. Merge into final output
    result: Dict[str, Any] = {
        "repository": repository_name,
        "root_cause": fix_proposal["root_cause"],
        "modified_files": fix_proposal["modified_files"],
        "fix_summary": fix_proposal["fix_summary"],
        "patch": fix_proposal["patch"],
        "confidence": fix_proposal["confidence"],
        "assumptions": fix_proposal["assumptions"],
        "analysis_summary": analysis.get("analysis_summary", ""),
        "error_category": analysis["error_category"],
        "raw_error_message": analysis.get("raw_error_message", ""),
    }

    # Merge retrieved context files from both phases
    combined_files = list(set(
        analysis.get("retrieved_context_files", [])
    ))
    result["retrieved_context_files"] = combined_files

    # 4. Emit fix_generated event
    if investigation_id:
        try:
            db = SessionLocal()
            inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
            if inv:
                inv.status = "fixing"
                inv.current_stage = "fix_generated"
                inv.current_stage_status = "completed"
                inv.summary = fix_proposal.get("fix_summary", "")
                db.commit()

            await event_manager.publish(
                event_type="fix_generated",
                data={
                    "repository": repository_name,
                    "fix_summary": fix_proposal.get("fix_summary", ""),
                    "modified_files": fix_proposal.get("modified_files", []),
                    "confidence": fix_proposal.get("confidence", 0.0),
                    "error_category": analysis.get("error_category", ""),
                },
                investigation_id=investigation_id,
            )
        except Exception as e:
            logger.warning(f"Failed to publish fix_generated event: {e}")
        finally:
            db.close()

    # 4. Persist fix artifact
    if investigation_id:
        try:
            db = SessionLocal()
            inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
            if inv:
                artifact = FixArtifact(
                    investigation_id=investigation_id,
                    fix_summary=fix_proposal.get("fix_summary", ""),
                    root_cause=fix_proposal.get("root_cause", ""),
                    confidence_score=fix_proposal.get("confidence", 0.0),
                    files_modified=json.dumps(fix_proposal.get("modified_files", [])),
                    patch_content=fix_proposal.get("patch", ""),
                    branch_name=None,
                    dry_run=True,
                    status="generated",
                    generated_at=datetime.now(timezone.utc),
                )
                db.add(artifact)
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist fix artifact: {e}")
        finally:
            db.close()

    # 5. Apply patch (dry-run by default)
    if investigation_id and fix_proposal.get("patch"):
        try:
            installation_token = None
            db = SessionLocal()
            try:
                inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
                if inv and inv.repository_id:
                    from app.database.models import Repository, GitHubInstallation
                    repo = db.query(Repository).filter(Repository.id == inv.repository_id).first()
                    if repo and repo.github_installation_id:
                        install = db.query(GitHubInstallation).filter(
                            GitHubInstallation.id == repo.github_installation_id
                        ).first()
                        if install:
                            from app.services.github_app import get_installation_token
                            installation_token = get_installation_token(install.installation_id)
            finally:
                db.close()

            patch_result = await apply_patch_async(
                repo_full_name=repository_name,
                installation_token=installation_token or "",
                patch_content=fix_proposal.get("patch", ""),
                branch_name=None,
                dry_run=installation_token is None,
            )

            if patch_result.get("applied"):
                db = SessionLocal()
                try:
                    artifact = db.query(FixArtifact).filter(
                        FixArtifact.investigation_id == investigation_id
                    ).order_by(FixArtifact.id.desc()).first()
                    if artifact:
                        artifact.branch_name = patch_result.get("branch")
                        artifact.dry_run = False
                        artifact.status = "applied"
                        artifact.applied_at = datetime.now(timezone.utc)
                        artifact.files_modified = json.dumps(patch_result.get("files_modified", []))
                        db.commit()

                    await event_manager.publish(
                        event_type="patch_applied",
                        data={
                            "repository": repository_name,
                            "branch": patch_result.get("branch"),
                            "files_modified": patch_result.get("files_modified", []),
                            "dry_run": False,
                        },
                        investigation_id=investigation_id,
                    )
                except Exception as e:
                    logger.warning(f"Failed to update fix artifact after patch: {e}")
                finally:
                    db.close()

        except Exception as e:
            logger.warning(f"Failed to apply patch: {e}")

    logger.info(f"Fix generation workflow complete for '{repository_name}'")
    return result
