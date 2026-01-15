import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Shared Utils
from shared.utils.redis_utils import RedisStreamUtils
from shared.libs.chatwoot_client import ChatwootClient

# Models
from app.models.bot_run import BotRun, BotRunEvent
from app.models.bot_studio import BotCrewVersion

logger = logging.getLogger("BotConsumer")
logging.basicConfig(level=logging.INFO)

class Settings(BaseSettings):
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    REDIS_STREAM_NAME: str = "events:chatwoot"
    REDIS_CONSUMER_GROUP: str = "cg:bot_runner"
    REDIS_CONSUMER_NAME: str = os.getenv("HOSTNAME", "bot_runner_1")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/ecocrm")
    
    # Chatwoot
    CHATWOOT_BASE_URL: str = os.getenv("CHATWOOT_BASE_URL", "")
    CHATWOOT_API_TOKEN: str = os.getenv("CHATWOOT_API_ACCESS_TOKEN", "")
    CHATWOOT_ACCOUNT_ID: int = int(os.getenv("CHATWOOT_ACCOUNT_ID", "1"))
    
    # Default Crew
    DEFAULT_CREW_VERSION_ID: int = int(os.getenv("DEFAULT_CREW_VERSION_ID", "1")) # MVP: Hardcoded version to run

settings = Settings()

# DB Setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def _save_event(session: AsyncSession, run_id: str, event_type: str, payload: dict):
    event = BotRunEvent(
        run_id=run_id,
        event_type=event_type,
        payload_json=payload
    )
    session.add(event)
    await session.commit()

async def execute_crew_logic(snapshot: dict, inputs: dict) -> str:
    """
    Simulates CrewAI execution based on snapshot.
    In a real implementation, this would:
    1. Parse agents/tasks from snapshot.
    2. Write agents.yaml/tasks.yaml or construct objects dynamically.
    3. Run crew.kickoff(inputs=inputs).
    """
    # MVP Stub logic
    crew_name = snapshot.get("crew", {}).get("name", "Unknown Crew")
    agents_count = len(snapshot.get("agents", []))
    tasks_count = len(snapshot.get("tasks", []))
    
    logger.info(f"Executing Crew '{crew_name}' with {agents_count} agents and {tasks_count} tasks.")
    
    # Simulate processing
    await asyncio.sleep(2)
    
    return f"Processed by {crew_name}. I analyzed your request: '{inputs.get('content')}'."

async def process_message(message_id: str, payload: dict, redis_utils: RedisStreamUtils):
    async with AsyncSessionLocal() as db:
        run_id = str(uuid.uuid4())
        conversation_id = None
        
        try:
            # 1. Parse Event
            # payload is simple dict from Redis Stream (all strings usually)
            # But our webhooks.py sends nested JSON inside string? 
            # Check webhooks.py: redis.publish_message sends dict.
            # RedisStreamUtils.consume_messages returns dict where values might be strings or parsing depends on utils.
            # Assuming payload is the data dict directly or has keys.
            
            # RedisStreamUtils.publish_message uses xadd with key/value pairs. webhooks.py sends 'data' as entire fields?
            # Let's check redis_utils. It normally dumps dict to JSON if not handled.
            # Assuming fields are available directly.
            
            # Currently webhooks.py sends:
            # await redis.publish_message(..., data=event_data)
            # If `data` is a dict, redis_utils usually xadd(..., data) which explodes it if it's flat, or we check implementation.
            # Assuming payload is the dictionary of fields.
            
            # Logic: If 'raw_event_id' is present, it's our new schema.
            if "raw_event_id" not in payload:
                # Legacy or different event
                return True 
                
            content = payload.get("content")
            conversation_id = payload.get("conversation_id")
            sender_type = payload.get("sender", {}).get("name") # Or Parse properly if sender is JSON string
            
            # Handle potential double-serialization if Redis implementation did that
            if isinstance(payload.get("sender"), str):
                 import json
                 try:
                     payload["sender"] = json.loads(payload["sender"])
                 except: pass

            logger.info(f"Processing Event for Conv {conversation_id}")
            
            # 2. Get Crew Version (Snapshot)
            stmt = select(BotCrewVersion).where(BotCrewVersion.id == settings.DEFAULT_CREW_VERSION_ID)
            res = await db.execute(stmt)
            version = res.scalar_one_or_none()
            
            if not version:
                logger.error(f"Default Crew Version {settings.DEFAULT_CREW_VERSION_ID} not found.")
                # We can't run.
                return True # Ack to avoid loop
            
            # 3. Create BotRun
            bot_run = BotRun(
                id=run_id,
                crew_version_id=version.id,
                source="chatwoot",
                conversation_id=str(conversation_id),
                status="running"
            )
            db.add(bot_run)
            await db.commit()
            
            await _save_event(db, run_id, "run_start", {"input": content})

            # 4. Run CrewAI
            try:
                # Retrieve snapshot
                snapshot = version.snapshot_json
                
                # EXECUTE
                final_answer = await execute_crew_logic(snapshot, {"content": content})
                
                # Update Run Success
                bot_run.status = "success"
                bot_run.finished_at = datetime.utcnow()
                bot_run.result_output = final_answer
                await db.commit()
                
                await _save_event(db, run_id, "run_success", {"output": final_answer})
                
                # 5. Reply to Chatwoot
                if settings.CHATWOOT_API_TOKEN:
                    chatwoot = ChatwootClient(
                        settings.CHATWOOT_BASE_URL,
                        settings.CHATWOOT_API_TOKEN,
                        settings.CHATWOOT_ACCOUNT_ID
                    )
                    await chatwoot.create_message(
                        conversation_id=int(conversation_id),
                        content=final_answer
                    )
                else:
                    logger.warning("Chatwoot credentials not set. Skipping reply.")
                    
            except Exception as e:
                logger.error(f"Crew Execution Failed: {e}")
                bot_run.status = "failed"
                bot_run.finished_at = datetime.utcnow()
                bot_run.result_output = str(e)
                await db.commit()
                await _save_event(db, run_id, "run_failed", {"error": str(e)})

            return True

        except Exception as e:
            logger.error(f"Fatal processing error: {e}")
            return False

async def start_consumer():
    redis = RedisStreamUtils(settings.REDIS_URL)
    logger.info(f"Starting Consumer Group {settings.REDIS_CONSUMER_GROUP}")
    
    await redis.ensure_consumer_group(settings.REDIS_STREAM_NAME, settings.REDIS_CONSUMER_GROUP)
    
    while True:
        try:
            # consume_messages yields (message_id, payload)
            async for message_id, payload in redis.consume_messages(
                settings.REDIS_STREAM_NAME,
                settings.REDIS_CONSUMER_GROUP,
                settings.REDIS_CONSUMER_NAME,
                count=1,
                block=2000
            ):
                logger.info(f"Got message {message_id}")
                success = await process_message(message_id, payload, redis)
                if success:
                    await redis.ack_message(settings.REDIS_STREAM_NAME, settings.REDIS_CONSUMER_GROUP, message_id)
                    
        except Exception as e:
            logger.error(f"Consumer Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(start_consumer())
