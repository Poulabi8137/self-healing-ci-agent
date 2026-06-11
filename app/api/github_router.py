"""GitHub management API — installations, repositories, activation."""
from fastapi import APIRouter, HTTPException, Depends

from app.auth.dependencies import get_current_jwt_user
from app.database.models import User, GitHubInstallation, Repository
from app.database.db import SessionLocal
from app.services.github_app import (
    get_installation_token_async,
    list_installation_repos_async,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/github")


@router.get("/installations")
async def list_installations(user: User = Depends(get_current_jwt_user)):
    """List GitHub App installations linked to this user."""
    db = SessionLocal()
    try:
        installations = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.user_id == user.id)
            .order_by(GitHubInstallation.created_at.desc())
            .all()
        )
        return {
            "installations": [
                {
                    "id": inst.id,
                    "installation_id": inst.installation_id,
                    "account_login": inst.account_login,
                    "account_type": inst.account_type,
                    "account_avatar": inst.account_avatar,
                    "account_url": inst.account_url,
                    "created_at": inst.created_at.isoformat() if inst.created_at else None,
                }
                for inst in installations
            ]
        }
    finally:
        db.close()


@router.get("/installations/{installation_id}/repos")
async def list_installations_repos(
    installation_id: int,
    user: User = Depends(get_current_jwt_user),
):
    """List repositories available for a given installation."""
    db = SessionLocal()
    try:
        inst = (
            db.query(GitHubInstallation)
            .filter(
                GitHubInstallation.id == installation_id,
                GitHubInstallation.user_id == user.id,
            )
            .first()
        )
        if not inst:
            raise HTTPException(status_code=404, detail="Installation not found")
    finally:
        db.close()

    try:
        token = await get_installation_token_async(inst.installation_id)
        repos = await list_installation_repos_async(token)
    except Exception as e:
        logger.error(f"Failed to list repos for installation {installation_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch repositories from GitHub")

    db = SessionLocal()
    try:
        known = {
            r.full_name: r
            for r in db.query(Repository).filter(Repository.github_installation_id == installation_id).all()
        }
    finally:
        db.close()

    return {
        "repositories": [
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "url": repo.get("html_url"),
                "default_branch": repo.get("default_branch"),
                "is_active": known.get(repo["full_name"], Repository()).is_active if repo["full_name"] in known else False,
                "in_db": repo["full_name"] in known,
            }
            for repo in repos
        ]
    }


@router.post("/installations/{installation_id}/sync")
async def sync_installation_repos(
    installation_id: int,
    user: User = Depends(get_current_jwt_user),
):
    """Sync repositories from a GitHub App installation into the local DB."""
    db = SessionLocal()
    try:
        inst = (
            db.query(GitHubInstallation)
            .filter(
                GitHubInstallation.id == installation_id,
                GitHubInstallation.user_id == user.id,
            )
            .first()
        )
        if not inst:
            raise HTTPException(status_code=404, detail="Installation not found")
    finally:
        db.close()

    try:
        token = await get_installation_token_async(inst.installation_id)
        repos = await list_installation_repos_async(token)
    except Exception as e:
        logger.error(f"Failed to sync repos for installation {installation_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch repositories from GitHub")

    db = SessionLocal()
    try:
        synced = 0
        for repo_data in repos:
            full_name = repo_data["full_name"]
            existing = db.query(Repository).filter(Repository.full_name == full_name).first()
            if existing:
                existing.github_installation_id = installation_id
                existing.url = repo_data.get("html_url")
                existing.default_branch = repo_data.get("default_branch", "main")
            else:
                repo = Repository(
                    name=repo_data["name"],
                    full_name=full_name,
                    url=repo_data.get("html_url"),
                    default_branch=repo_data.get("default_branch", "main"),
                    github_installation_id=installation_id,
                )
                db.add(repo)
            synced += 1
        db.commit()
        logger.info(f"Synced {synced} repos for installation {installation_id}")
        return {"synced": synced}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/repositories/{repo_id}/activate")
async def activate_repository(
    repo_id: int,
    user: User = Depends(get_current_jwt_user),
):
    """Enable monitoring for a repository."""
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        repo.is_active = True
        db.commit()
        logger.info(f"Repository activated: {repo.full_name}")
        return {"status": "activated", "full_name": repo.full_name}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/repositories/{repo_id}/deactivate")
async def deactivate_repository(
    repo_id: int,
    user: User = Depends(get_current_jwt_user),
):
    """Disable monitoring for a repository."""
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        repo.is_active = False
        db.commit()
        logger.info(f"Repository deactivated: {repo.full_name}")
        return {"status": "deactivated", "full_name": repo.full_name}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
