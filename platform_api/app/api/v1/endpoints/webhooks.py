from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging
import json
from datetime import datetime

from app.core.config import settings
from shared.utils.redis_utils import RedisStreamUtils

router = APIRouter()
logger = logging.getLogger(__name__)

# Basic token for dev purposes. In prod, this should be a secure random string or checking against DB.
WEBHOOK_TOKEN = "SEU_TOKEN" 

@router.post("/chatwoot")
async def chatwoot_webhook(
    request: Request,
    t: str = Query(..., description="Validation token"),
) -> Any:
    """
    Receive webhooks from Chatwoot.
    Validates token, filters 'message_created', and publishes to Redis.
    """
    # 1. Validate Token
    if t != WEBHOOK_TOKEN:
        logger.warning(f"Invalid webhook token attempted: {t}")
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event")
    
    # 2. Filter Event Type
    if event_type != "message_created":
        logger.info(f"Ignored event type: {event_type}")
        return {"status": "ignored", "reason": "event_type"}

    # 3. Extract Data
    try:
        # Structure based on Chatwoot payload
        # https://www.chatwoot.com/docs/product/others/webhooks/payloads
        data = payload.get("data", {})
        conversation = data.get("conversation", {})
        sender = data.get("sender", {})
        
        # Verify if it's an incoming message (from user) or outgoing (from agent/bot)
        # We usually care about incoming for the bot to run.
        message_type = payload.get("message_type") # incoming/outgoing
        
        event_data = {
            "account_id": payload.get("account", {}).get("id"),
            "inbox_id": data.get("inbox", {}).get("id"),
            "conversation_id": conversation.get("id"),
            "message_id": data.get("id"),
            "message_type": message_type,
            "sender": {
                "id": sender.get("id"),
                "name": sender.get("name"),
                "phone_number": sender.get("phone_number")
            },
            "content": data.get("content"),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Processing message_created: {event_data['message_id']} from {event_data['sender']['name']}")

        # 4. Publish to Redis Stream
        redis = RedisStreamUtils(settings.REDIS_URL)
        await redis.publish_message(
            stream_name=settings.REDIS_STREAM_NAME,
            data=event_data
        )
        
        return {"status": "processed", "message_id": event_data["message_id"]}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")
