"""Events router — SSE streaming and event history."""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_jwt_user
from app.database.db import SessionLocal
from app.database.models import InvestigationEvent, User
from app.services.event_manager import event_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/events")


@router.get("/stream")
async def event_stream(request: Request):
    """SSE endpoint — streams real-time investigation events to authenticated users.

    Admins receive all events. Non-admin users receive events for repos linked
    to their GitHub installations.
    """
    user: User = await get_current_jwt_user(request)
    user_id = user.id
    queue = await event_manager.subscribe(user_id)

    async def generate():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: {event['event_type']}\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await event_manager.unsubscribe(user_id)
            logger.debug(f"SSE client disconnected: user_id={user_id}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def event_history(
    request: Request,
    since: str | None = Query(None, description="ISO 8601 timestamp — return events after this time"),
    limit: int = Query(50, ge=1, le=200),
):
    """Return persisted events for backfill after SSE reconnection."""
    user: User = await get_current_jwt_user(request)

    db = SessionLocal()
    try:
        query = db.query(InvestigationEvent).order_by(InvestigationEvent.created_at.desc())

        if user.role != "admin":
            from app.database.models import Repository, GitHubInstallation, Investigation
            installations = db.query(GitHubInstallation).filter(
                GitHubInstallation.user_id == user.id
            ).all()
            inst_ids = [i.id for i in installations]
            repos = db.query(Repository).filter(
                Repository.github_installation_id.in_(inst_ids)
            ).all() if inst_ids else []
            repo_ids = [r.id for r in repos]
            investigations = db.query(Investigation).filter(
                Investigation.repository_id.in_(repo_ids)
            ).all() if repo_ids else []
            inv_ids = [inv.id for inv in investigations]
            query = query.filter(
                InvestigationEvent.investigation_id.in_(inv_ids)
            ) if inv_ids else query.filter(False)

        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                query = query.filter(InvestigationEvent.created_at > since_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' format. Use ISO 8601.")

        events = query.limit(limit).all()

        return _serialize_events(events)
    finally:
        db.close()


@router.get("/investigation/{investigation_id}")
async def investigation_events(
    investigation_id: int,
    request: Request,
):
    """Return all events for a specific investigation, ordered by creation time."""
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

        events = (
            db.query(InvestigationEvent)
            .filter(InvestigationEvent.investigation_id == investigation_id)
            .order_by(InvestigationEvent.created_at.asc())
            .all()
        )

        return _serialize_events(events)
    finally:
        db.close()


def _serialize_events(events: list[InvestigationEvent]) -> list[dict]:
    """Shared serializer for InvestigationEvent rows."""
    return [
        {
            "id": e.id,
            "investigation_id": e.investigation_id,
            "event_type": e.event_type,
            "data": json.loads(e.data) if isinstance(e.data, str) else e.data,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
