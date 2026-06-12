"""Event manager — routes events to SSE clients and persists to investigation_events."""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from app.database.db import SessionLocal
from app.database.models import InvestigationEvent, User


class EventManager:
    """Manages per-user event queues for SSE streaming.

    - In-memory dict[user_id, asyncio.Queue] per connected SSE client
    - `publish()` persists to DB and pushes to connected queues
    - `publish_sync()` for synchronous callers (webhook handler)
    - Queue max size 100; oldest dropped if full
    """
    def __init__(self):
        self._queues: dict[int, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    def _get_user_ids_for_event(self, event_type: str, investigation_id: int | None = None, user_ids: list[int] | None = None) -> list[int]:
        if user_ids is not None:
            return user_ids
        db = SessionLocal()
        try:
            admins = db.query(User).filter(User.role == "admin").all()
            admin_ids = [u.id for u in admins]
            if investigation_id:
                from app.database.models import Investigation
                investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
                if investigation:
                    from app.database.models import Repository
                    repo = db.query(Repository).filter(Repository.id == investigation.repository_id).first()
                    if repo and repo.github_installation_id:
                        from app.database.models import GitHubInstallation
                        inst = db.query(GitHubInstallation).filter(GitHubInstallation.id == repo.github_installation_id).first()
                        if inst:
                            return list(set(admin_ids + [inst.user_id]))
            return list(set(admin_ids))
        finally:
            db.close()

    def publish_sync(
        self,
        event_type: str,
        data: dict[str, Any],
        investigation_id: int | None = None,
        user_ids: list[int] | None = None,
        db=None,
    ) -> dict:
        """Publish an event from a synchronous context.

        If `db` is provided, the event is added to that session (caller manages commit).
        Otherwise, a new session is created and committed.
        Returns the payload dict (for SSE push). Does NOT return the DB event.
        """
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True

        try:
            event = InvestigationEvent(
                investigation_id=investigation_id,
                event_type=event_type,
                data=json.dumps(data),
            )
            db.add(event)
            if own_session:
                db.commit()
                db.refresh(event)
            created_at = event.created_at if event.created_at else datetime.now(timezone.utc)
            payload = {
                "id": getattr(event, "id", 0),
                "investigation_id": investigation_id,
                "event_type": event_type,
                "data": data,
                "created_at": created_at.isoformat(),
            }

            target_ids = self._get_user_ids_for_event(event_type, investigation_id, user_ids)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._push_to_queues(target_ids, payload))
                else:
                    loop.run_until_complete(self._push_to_queues(target_ids, payload))
            except RuntimeError:
                pass

            # Fire notification dispatch as background task
            self._fire_notification(event_type, payload["data"], investigation_id)

            return payload
        except Exception:
            if own_session:
                db.rollback()
            raise
        finally:
            if own_session:
                db.close()

    async def publish(
        self,
        event_type: str,
        data: dict[str, Any],
        investigation_id: int | None = None,
        user_ids: list[int] | None = None,
    ) -> dict:
        """Publish an event from an async context. Always creates its own session."""
        db = SessionLocal()
        try:
            event = InvestigationEvent(
                investigation_id=investigation_id,
                event_type=event_type,
                data=json.dumps(data),
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            created_at = event.created_at if event.created_at else datetime.now(timezone.utc)
            payload = {
                "id": event.id,
                "investigation_id": investigation_id,
                "event_type": event_type,
                "data": data,
                "created_at": created_at.isoformat(),
            }

            if user_ids is None:
                user_ids = self._get_user_ids_for_event(event_type, investigation_id)

            await self._push_to_queues(user_ids, payload)

            # Fire notification dispatch
            self._fire_notification(event_type, payload["data"], investigation_id)

            return payload
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def _push_to_queues(self, user_ids: list[int], payload: dict) -> None:
        async with self._lock:
            for uid in user_ids:
                if uid in self._queues:
                    try:
                        self._queues[uid].put_nowait(payload)
                    except asyncio.QueueFull:
                        try:
                            self._queues[uid].get_nowait()
                            self._queues[uid].put_nowait(payload)
                        except (asyncio.QueueEmpty, asyncio.QueueFull):
                            pass

    async def subscribe(self, user_id: int) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._queues[user_id] = queue
        return queue

    async def unsubscribe(self, user_id: int) -> None:
        async with self._lock:
            self._queues.pop(user_id, None)

    def _fire_notification(self, event_type: str, data: dict[str, Any], investigation_id: int | None = None) -> None:
        """Fire-and-forget notification dispatch for the given event."""
        from app.services.notification_dispatcher import process_event
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(process_event(event_type, {"investigation_id": investigation_id, **data}))
            else:
                loop.run_until_complete(process_event(event_type, {"investigation_id": investigation_id, **data}))
        except RuntimeError:
            pass
        except Exception:
            pass


event_manager = EventManager()
