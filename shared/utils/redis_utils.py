import os
import logging
import asyncio
from typing import Dict, Any, Optional
import redis.asyncio as redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)

class RedisStreamUtils:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        if not self.client:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def ensure_consumer_group(self, stream_name: str, group_name: str, start_id: str = "0"):
        """
        Ensures the stream and consumer group exist.
        Using 'MKSTREAM' to create the stream if it doesn't exist.
        """
        if not self.client:
            await self.connect()
        
        try:
            await self.client.xgroup_create(stream_name, group_name, id=start_id, mkstream=True)
            logger.info(f"Created consumer group '{group_name}' for stream '{stream_name}'")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{group_name}' already exists for stream '{stream_name}'")
            else:
                logger.error(f"Error creating consumer group: {e}")
                raise

    async def publish_event(self, stream_name: str, fields: Dict[str, Any]):
        """
        Publishes an event to the specified stream.
        """
        if not self.client:
            await self.connect()
        
        try:
            message_id = await self.client.xadd(stream_name, fields)
            logger.debug(f"Published event to {stream_name}: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish event to {stream_name}: {e}")
            raise

    async def consume_messages(self, stream_name: str, group_name: str, consumer_name: str, batch_size: int = 10, block_ms: int = 5000):
        """
        Consumes messages from a stream using a consumer group.
        Yields (message_id, fields) tuples.
        """
        if not self.client:
            await self.connect()

        try:
            # XREADGROUP via '>' to get new messages
            streams = {stream_name: ">"}
            messages = await self.client.xreadgroup(group_name, consumer_name, streams, count=batch_size, block=block_ms)
            
            if not messages:
                return

            for stream, payload in messages:
                for message_id, fields in payload:
                    yield message_id, fields

        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            # Depending on resilience strategy, might want to re-raise or just log
            raise

    async def ack_message(self, stream_name: str, group_name: str, message_id: str):
        """
        Acknowledges a processed message.
        """
        if not self.client:
            await self.connect()
            
        await self.client.xack(stream_name, group_name, message_id)
        logger.debug(f"Acked message {message_id} in group {group_name}")

# Global instance pattern or factory could be used
redis_utils = RedisStreamUtils()
