from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.data_hub import RawChatwootEvent
from shared.utils.redis_utils import RedisStreamUtils

router = APIRouter()
logger = logging.getLogger(__name__)

# Basic token for dev purposes.
WEBHOOK_TOKEN = "SEU_TOKEN" 

@router.post("/chatwoot")
async def chatwoot_webhook(
    request: Request,
    t: str = Query(..., description="Validation token"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Receive webhooks from Chatwoot.
    1. Validates token.
    2. Persists RAW event to DB.
    3. Filters 'message_created'.
    4. Publishes normalized event to Redis.
    """
    # 1. Validate Token
    if t != WEBHOOK_TOKEN:
        logger.warning(f"Invalid webhook token attempted: {t}")
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 2. Persist RAW Event
    event_type = payload.get("event")
    account_id = payload.get("account", {}).get("id")
    
    # Extract IDs if available just for indexing columns
    data = payload.get("data", {})
    conversation_id = data.get("conversation", {}).get("id")
    message_id = data.get("id")
    
    # Use consolidated RawChatwootEvent
    # Note: received_at is default now
    raw_event = RawChatwootEvent(
        event_name=event_type,
        account_id=account_id,
        inbox_id=data.get("inbox", {}).get("id"), # Added inbox_id mapping
        conversation_id=conversation_id,
        message_id=message_id,
        payload_json=payload,
        headers_json=dict(request.headers),
        is_valid=True 
    )
    db.add(raw_event)
    await db.commit()
    await db.refresh(raw_event)
    
    logger.info(f"Persisted Raw Event ID: {raw_event.id} - Type: {event_type}")

    # 3. Filter Event Type
    if event_type != "message_created":
        logger.info(f"Ignored event type: {event_type}")
        return {"status": "ignored", "reason": "event_type"}

    # 4. Extract Data & Publish
    try:
        conversation = data.get("conversation", {})
        sender = data.get("sender", {})
        message_type = payload.get("message_type") # incoming/outgoing
        
        event_data = {
            "raw_event_id": raw_event.id, # Link to raw storage
            "account_id": account_id,
            "inbox_id": data.get("inbox", {}).get("id"),
            "conversation_id": conversation.get("id"),
            "message_id": message_id,
            "message_type": message_type,
            "sender": {
                "id": sender.get("id"),
                "name": sender.get("name"),
                "phone_number": sender.get("phone_number")
            },
            "content": data.get("content"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Publishing message_created: {event_data['message_id']} (Raw ID: {raw_event.id})")

        # Publish to Redis Stream
        redis = RedisStreamUtils(settings.REDIS_URL)
        await redis.publish_message(
            stream_name=settings.REDIS_STREAM_NAME,
            data=event_data
        )
        
        return {"status": "processed", "message_id": event_data["message_id"], "raw_id": raw_event.id}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Optionally mark raw event as invalid or add error note
        raw_event.is_valid = False
        raw_event.validation_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail="Internal processing error")
