"""Slack integration API router — connect/disconnect, channel selection."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth.dependencies import get_current_jwt_user
from app.database.db import SessionLocal
from app.database.models import SlackWorkspace, User
from app.services.slack_service import list_slack_channels

router = APIRouter()


class ConnectRequest(BaseModel):
    code: str
    redirect_uri: str


class ChannelSelect(BaseModel):
    channel_id: str
    channel_name: str


@router.post("/slack/connect")
async def slack_connect(
    body: ConnectRequest,
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """Exchange OAuth code for Slack token and persist workspace."""
    from app.services.slack_service import exchange_oauth_code

    success, result = await exchange_oauth_code(body.code, body.redirect_uri)
    if not success:
        raise HTTPException(status_code=400, detail=f"Slack OAuth failed: {result}")

    db = SessionLocal()
    try:
        existing = db.query(SlackWorkspace).filter(SlackWorkspace.user_id == user.id).first()
        if existing:
            existing.workspace_id = result["workspace_id"]
            existing.workspace_name = result["workspace_name"]
            existing.access_token = result["access_token"]
            existing.updated_at = datetime.now(timezone.utc)
        else:
            existing = SlackWorkspace(
                user_id=user.id,
                workspace_id=result["workspace_id"],
                workspace_name=result["workspace_name"],
                access_token=result["access_token"],
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        return {
            "workspace_id": existing.workspace_id,
            "workspace_name": existing.workspace_name,
            "selected_channel_id": existing.selected_channel_id,
            "selected_channel_name": existing.selected_channel_name,
        }
    finally:
        db.close()


@router.post("/slack/disconnect")
async def slack_disconnect(
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """Remove the Slack workspace connection for the authenticated user."""
    db = SessionLocal()
    try:
        workspace = db.query(SlackWorkspace).filter(SlackWorkspace.user_id == user.id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="No Slack workspace connected")
        db.delete(workspace)
        db.commit()
        return {"status": "disconnected"}
    finally:
        db.close()


@router.get("/slack/status")
async def slack_status(
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """Return the current Slack connection status for the authenticated user."""
    db = SessionLocal()
    try:
        workspace = db.query(SlackWorkspace).filter(SlackWorkspace.user_id == user.id).first()
        if not workspace:
            return {"connected": False}
        return {
            "connected": True,
            "workspace_id": workspace.workspace_id,
            "workspace_name": workspace.workspace_name,
            "selected_channel_id": workspace.selected_channel_id,
            "selected_channel_name": workspace.selected_channel_name,
        }
    finally:
        db.close()


@router.get("/slack/channels")
async def slack_channels(
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """List available Slack channels for the connected workspace."""
    db = SessionLocal()
    try:
        workspace = db.query(SlackWorkspace).filter(SlackWorkspace.user_id == user.id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="No Slack workspace connected")

        success, result = await list_slack_channels(workspace.access_token)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to list channels: {result}")

        return {"channels": result}
    finally:
        db.close()


@router.put("/slack/channel")
async def slack_select_channel(
    body: ChannelSelect,
    request: Request,
    user: User = Depends(get_current_jwt_user),
):
    """Save the preferred Slack channel for notifications."""
    db = SessionLocal()
    try:
        workspace = db.query(SlackWorkspace).filter(SlackWorkspace.user_id == user.id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="No Slack workspace connected")

        workspace.selected_channel_id = body.channel_id
        workspace.selected_channel_name = body.channel_name
        workspace.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "selected_channel_id": workspace.selected_channel_id,
            "selected_channel_name": workspace.selected_channel_name,
        }
    finally:
        db.close()
