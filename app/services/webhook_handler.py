"""Webhook handler — GitHub webhook verification, routing, and processing."""
import hashlib
import hmac
import json
from datetime import datetime, timezone

from app.config.settings import settings
from app.database.db import SessionLocal
from app.database.models import WebhookEvent, Repository, Failure, Investigation, GitHubInstallation
from app.services.github_app import get_installation_token, get_workflow_run, get_workflow_run_jobs
from app.services.event_manager import event_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    if not signature_header or not settings.github_app_webhook_secret:
        return False
    expected = "sha256=" + hmac.new(
        settings.github_app_webhook_secret.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def process_webhook(
    event_type: str,
    delivery_id: str,
    payload: dict,
) -> dict:
    """Route and process a verified webhook event."""
    db = SessionLocal()
    try:
        existing = db.query(WebhookEvent).filter(WebhookEvent.delivery_id == delivery_id).first()
        if existing:
            logger.info(f"Duplicate webhook delivery: {delivery_id} — skipping")
            return {"status": "skipped", "reason": "duplicate"}
    finally:
        db.close()

    db = SessionLocal()
    try:
        event = WebhookEvent(
            delivery_id=delivery_id,
            event_type=event_type,
            action=payload.get("action"),
            payload=json.dumps(payload),
            processed=False,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    try:
        if event_type == "workflow_run":
            result = _handle_workflow_run(payload, event_id)
        elif event_type == "installation":
            result = _handle_installation(payload, event_id)
        elif event_type == "installation_repositories":
            result = _handle_installation_repos(payload, event_id)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            result = {"status": "unhandled", "event_type": event_type}

        db = SessionLocal()
        try:
            evt = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
            if evt:
                evt.processed = True
                evt.processed_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

        return result
    except Exception as e:
        logger.error(f"Failed to process webhook {delivery_id}: {e}")
        db = SessionLocal()
        try:
            evt = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
            if evt:
                evt.error = str(e)[:500]
                db.commit()
        finally:
            db.close()
        return {"status": "error", "error": str(e)}


def _handle_workflow_run(payload: dict, event_id: int) -> dict:
    """Process workflow_run webhook — detect failures and trigger investigations."""
    workflow_run = payload.get("workflow_run", {})
    repository = payload.get("repository", {})
    conclusion = workflow_run.get("conclusion")

    if conclusion != "failure":
        return {"status": "ignored", "reason": f"conclusion={conclusion}"}

    full_name = repository.get("full_name")
    run_id = workflow_run.get("id")
    workflow_name = workflow_run.get("name")

    if not full_name or not run_id:
        return {"status": "ignored", "reason": "missing repository or run_id"}

    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.full_name == full_name).first()
        if not repo:
            logger.info(f"Repository not found in DB: {full_name}")
            return {"status": "ignored", "reason": "repository not found"}
        if not repo.is_active:
            logger.info(f"Repository not active: {full_name}")
            return {"status": "ignored", "reason": "repository not active"}

        existing_failure = db.query(Failure).filter(
            Failure.run_id == str(run_id),
            Failure.repository_id == repo.id,
        ).first()
        if existing_failure:
            return {"status": "skipped", "reason": "duplicate failure"}

        error_message = workflow_run.get("conclusion")
        job_name = None
        step_name = None

        if repo.github_installation_id:
            try:
                inst = db.query(GitHubInstallation).filter(
                    GitHubInstallation.id == repo.github_installation_id
                ).first()
                if inst:
                    token = get_installation_token(inst.installation_id)
                    run_data = get_workflow_run(token, full_name, run_id)
                    if run_data:
                        error_message = run_data.get("conclusion", conclusion)
                    jobs = get_workflow_run_jobs(token, full_name, run_id)
                    if jobs:
                        failed_job = next((j for j in jobs if j.get("conclusion") == "failure"), None)
                        if failed_job:
                            job_name = failed_job.get("name")
                            steps = failed_job.get("steps", [])
                            failed_step = next((s for s in steps if s.get("conclusion") == "failure"), None)
                            if failed_step:
                                step_name = failed_step.get("name")
            except Exception as e:
                logger.warning(f"Failed to fetch run details from GitHub: {e}")

        failure = Failure(
            repository_id=repo.id,
            github_installation_id=repo.github_installation_id,
            workflow_name=workflow_name,
            run_id=str(run_id),
            job_name=job_name,
            step_name=step_name,
            error_message=error_message,
            status="detected",
        )
        db.add(failure)
        db.flush()

        repo.last_workflow_status = "failure"
        repo.last_workflow_run_at = datetime.now(timezone.utc)
        repo.failure_count = (repo.failure_count or 0) + 1

        investigation = Investigation(
            failure_id=failure.id,
            repository_id=repo.id,
            status="detecting",
        )
        db.add(investigation)
        db.flush()

        event_manager.publish_sync(
            event_type="failure_detected",
            data={
                "repository": full_name,
                "workflow": workflow_name,
                "run_id": run_id,
                "failure_id": failure.id,
            },
            investigation_id=investigation.id,
            db=db,
        )
        db.commit()

        logger.info(f"Failure detected: {full_name} workflow={workflow_name} run_id={run_id} "
                     f"failure_id={failure.id} investigation_id={investigation.id}")

        return {
            "status": "investigation_created",
            "failure_id": failure.id,
            "investigation_id": investigation.id,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _handle_installation(payload: dict, event_id: int) -> dict:
    """Process installation webhook — track GitHub App installations."""
    action = payload.get("action")
    installation = payload.get("installation", {})
    sender = payload.get("sender", {})

    if action == "created":
        account = installation.get("account", {})
        db = SessionLocal()
        try:
            existing = db.query(GitHubInstallation).filter(
                GitHubInstallation.installation_id == installation["id"]
            ).first()
            if existing:
                existing.account_login = account.get("login")
                existing.account_type = account.get("type")
                existing.account_avatar = account.get("avatar_url")
                existing.account_url = account.get("html_url")
                existing.github_id = sender.get("id")
            else:
                inst = GitHubInstallation(
                    installation_id=installation["id"],
                    account_login=account.get("login"),
                    account_type=account.get("type"),
                    account_avatar=account.get("avatar_url"),
                    account_url=account.get("html_url"),
                    github_id=sender.get("id"),
                )
                db.add(inst)
            db.commit()
            return {"status": "installation_recorded", "installation_id": installation["id"]}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    elif action == "deleted":
        db = SessionLocal()
        try:
            db.query(GitHubInstallation).filter(
                GitHubInstallation.installation_id == installation["id"]
            ).delete()
            db.commit()
            return {"status": "installation_removed"}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return {"status": "ignored", "action": action}


def _handle_installation_repos(payload: dict, event_id: int) -> dict:
    """Process installation_repositories webhook — sync repo list."""
    action = payload.get("action")
    installation = payload.get("installation", {})
    installation_id = installation.get("id")

    db = SessionLocal()
    try:
        gh_inst = db.query(GitHubInstallation).filter(
            GitHubInstallation.installation_id == installation_id
        ).first()
        if not gh_inst:
            return {"status": "ignored", "reason": "installation not found"}
        gh_inst_id = gh_inst.id
    finally:
        db.close()

    repos_added = payload.get("repositories_added", [])
    repos_removed = payload.get("repositories_removed", [])

    db = SessionLocal()
    try:
        for repo_data in repos_added:
            existing = db.query(Repository).filter(Repository.full_name == repo_data["full_name"]).first()
            if existing:
                existing.github_installation_id = gh_inst_id
            else:
                repo = Repository(
                    name=repo_data["name"],
                    full_name=repo_data["full_name"],
                    url=repo_data.get("html_url"),
                    github_installation_id=gh_inst_id,
                )
                db.add(repo)
        for repo_data in repos_removed:
            db.query(Repository).filter(
                Repository.full_name == repo_data["full_name"],
                Repository.github_installation_id == gh_inst_id,
            ).update({"github_installation_id": None})
        db.commit()
        return {
            "status": "synced",
            "added": len(repos_added),
            "removed": len(repos_removed),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
