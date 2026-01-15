import asyncio
import json
import logging
import os
from pydantic_settings import BaseSettings
from shared.utils.redis_utils import redis_utils

logger = logging.getLogger("BotConsumer")

class Settings(BaseSettings):
    REDIS_STREAM_NAME: str = "events:chatwoot"
    REDIS_CONSUMER_GROUP: str = "cg:bot_runner"
    REDIS_CONSUMER_NAME: str = os.getenv("HOSTNAME", "bot_runner_1")

settings = Settings()

async def process_message(message_id: str, payload: dict):
    """
    Process a single message from the stream.
    Placeholder for CrewAI integration.
    """
    try:
        data = json.loads(payload.get("payload", "{}"))
        logger.info(f"Processing message {message_id}: {data.get('content')} from {data.get('sender_type')}")
        
        # TODO: Integrate CrewAI here
        # crew = Crew(...)
        # result = crew.kickoff()
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        return True
    except Exception as e:
        logger.error(f"Failed to process message {message_id}: {e}")
        return False

async def start_consumer():
    """
    Main consumer loop.
    """
    logger.info(f"Starting Consumer: {settings.REDIS_CONSUMER_GROUP} - {settings.REDIS_CONSUMER_NAME}")
    
    # Ensure group exists
    await redis_utils.ensure_consumer_group(
        settings.REDIS_STREAM_NAME, 
        settings.REDIS_CONSUMER_GROUP
    )
    
    while True:
        try:
            async for message_id, fields in redis_utils.consume_messages(
                settings.REDIS_STREAM_NAME,
                settings.REDIS_CONSUMER_GROUP,
                settings.REDIS_CONSUMER_NAME,
                batch_size=1,
                block_ms=2000
            ):
                logger.info(f"Received message {message_id}")
                
                success = await process_message(message_id, fields)
                
                if success:
                    await redis_utils.ack_message(
                        settings.REDIS_STREAM_NAME,
                        settings.REDIS_CONSUMER_GROUP,
                        message_id
                    )
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            await asyncio.sleep(5)
