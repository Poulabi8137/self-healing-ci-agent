"""Webhook receiver — GitHub webhooks with HMAC verification and replay protection."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.services.webhook_handler import verify_signature, process_webhook
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/github")
async def github_webhook(request: Request):
    """Receive and process GitHub App webhooks."""
    body = await request.body()

    event_type = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not event_type or not delivery_id:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event or X-GitHub-Delivery header")

    if not verify_signature(body, signature):
        logger.warning(f"Webhook signature verification failed: delivery={delivery_id}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    logger.info(f"Webhook received: event={event_type} delivery={delivery_id}")

    result = process_webhook(
        event_type=event_type,
        delivery_id=delivery_id,
        payload=payload,
    )

    return JSONResponse(content=result)
