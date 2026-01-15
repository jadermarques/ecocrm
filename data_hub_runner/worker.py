import asyncio
import logging
import os
import sys
from datetime import datetime
from pydantic_settings import BaseSettings

# Ensure we can import from platform_api and shared
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_hub_runner.analytics import init_analytics_schema, refresh_marts

# ... (Previous Code)

async def process_conversation(session, client, conv, processed_count):
    """Process a single conversation: Upsert Conv, Msgs, Reports"""
    conv_id = conv['id']
    try:
        # 1. Upsert Conversation
        await upsert_conversation(session, conv)
        
        # 2. Fetch & Upsert Messages
        msgs_data = await client.get_messages(conv_id)
        messages = msgs_data.get('payload', [])
        for msg in messages:
            await upsert_message(session, msg)
            
        # 3. Fetch & Upsert Reporting Events
        try:
            report_data = await client.get_conversation_reporting_events(conv_id)
            if isinstance(report_data, list):
                await upsert_reporting_events(session, report_data)
        except Exception as e:
            logger.warning(f"Could not fetch reporting events for conv {conv_id}: {e}")

        return True
    
    except Exception as e:
        logger.error(f"Error processing conv {conv_id}: {e}")
        return False

async def run_backfill():
    """Main Backfill Logic"""
    logger.info("Starting Backfill...")
    client = ChatwootClient(
        base_url=settings.CHATWOOT_BASE_URL,
        api_access_token=settings.CHATWOOT_API_TOKEN,
        account_id=settings.CHATWOOT_ACCOUNT_ID
    )
    
    async with AsyncSessionLocal() as session:
        await init_analytics_schema(session)

        page = 1
        total_processed = 0
        
        while True:
            logger.info(f"Fetching Conversations Page {page}...")
            data = await client.list_conversations(page=page, status='all')
            conversations = data.get('data', {}).get('payload', [])
            meta = data.get('data', {}).get('meta', {})
            
            if not conversations:
                break
                
            for conv in conversations:
                if await process_conversation(session, client, conv, total_processed):
                    total_processed += 1

            await session.commit()
            
            current_page = meta.get('current_page', page)
            total_pages = meta.get('total_pages', page)
            if current_page >= total_pages:
                break
            page += 1
            
        logger.info(f"Backfill Complete. Processed {total_processed} conversations.")
        
        await refresh_marts(session)

async def main():
    logger.info(f"Data Hub Runner Started. Interval: {settings.DATA_HUB_BACKFILL_INTERVAL_SECONDS}s")
    
    # Run once at startup
    async with AsyncSessionLocal() as session:
        await init_analytics_schema(session)

    while True:
        try:
            await run_backfill()
        except Exception as e:
            logger.error(f"Backfill Job Failed: {e}")
        
        await asyncio.sleep(settings.DATA_HUB_BACKFILL_INTERVAL_SECONDS)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataHubRunner")

class Settings(BaseSettings):
    DATABASE_URL: str
    CHATWOOT_BASE_URL: str
    CHATWOOT_API_TOKEN: str # User token for API access (not the webhook token)
    CHATWOOT_ACCOUNT_ID: int
    DATA_HUB_BACKFILL_INTERVAL_SECONDS: int = 1800
    DATA_HUB_BACKFILL_DAYS_WINDOW: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# DB Setup
engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def upsert_conversation(session, conv_data):
    """Upsert Conversation Record"""
    stmt = pg_insert(RawChatwootConversation).values(
        conversation_id=conv_data['id'],
        account_id=conv_data['account_id'],
        inbox_id=conv_data['inbox_id'],
        status=conv_data['status'],
        assignee_id=conv_data['meta']['assignee']['id'] if conv_data.get('meta', {}).get('assignee') else None,
        contact_id=conv_data['meta']['sender']['id'] if conv_data.get('meta', {}).get('sender') else None,
        created_at_ts=datetime.fromtimestamp(conv_data['timestamp']), # Timestamp is unix
        updated_at_ts=datetime.now(), # Estimate or parse from payload if available
        payload_json=conv_data
    ).on_conflict_do_update(
        index_elements=['conversation_id'],
        set_={
            'status': conv_data['status'],
            'assignee_id': conv_data['meta']['assignee']['id'] if conv_data.get('meta', {}).get('assignee') else None,
            'updated_at_ts': datetime.now(),
            'payload_json': conv_data
        }
    )
    await session.execute(stmt)

async def upsert_message(session, msg_data):
    """Upsert Message Record"""
    stmt = pg_insert(RawChatwootMessage).values(
        message_id=msg_data['id'],
        conversation_id=msg_data['conversation_id'],
        account_id=msg_data['account_id'],
        inbox_id=msg_data['inbox_id'],
        message_type=msg_data['message_type'],
        content=msg_data.get('content'),
        private=msg_data.get('private', False),
        sender_type=msg_data.get('sender_type'), # User/Contact
        sender_id=msg_data.get('sender_id'), # or sender['id']
        created_at_ts=datetime.fromtimestamp(msg_data['created_at']),
        updated_at_ts=datetime.now(),
        payload_json=msg_data
    ).on_conflict_do_update(
        index_elements=['message_id'],
        set_={
            'content': msg_data.get('content'),
            'updated_at_ts': datetime.now(),
            'payload_json': msg_data
        }
    )
    await session.execute(stmt)

async def upsert_reporting_events(session, events):
    """Upsert Reporting Events"""
    for evt in events:
        stmt = pg_insert(RawChatwootReportingEvent).values(
            reporting_event_id=evt['id'],
            account_id=evt['account_id'],
            conversation_id=evt['conversation_id'],
            inbox_id=evt['inbox_id'],
            user_id=evt['user_id'],
            name=evt['name'],
            value_seconds=evt.get('value'), # 'value' often holds seconds
            value_business_hours_seconds=None, # Need to check payload structure
            event_start_time=datetime.fromtimestamp(evt['created_at']), # Using created_at as start?
            event_end_time=datetime.fromtimestamp(evt['updated_at']),
            created_at_ts=datetime.now(),
            updated_at_ts=datetime.now(),
            payload_json=evt
        ).on_conflict_do_update(
            index_elements=['reporting_event_id'],
            set_={'payload_json': evt, 'updated_at_ts': datetime.now()}
        )
        await session.execute(stmt)


async def run_backfill():
    """Main Backfill Logic"""
    logger.info("Starting Backfill...")
    client = ChatwootClient(
        base_url=settings.CHATWOOT_BASE_URL,
        api_access_token=settings.CHATWOOT_API_TOKEN,
        account_id=settings.CHATWOOT_ACCOUNT_ID
    )
    
    async with AsyncSessionLocal() as session:
        page = 1
        processed_count = 0
        
        while True:
            logger.info(f"Fetching Conversations Page {page}...")
            # Fetch all conversations (status='all')
            data = await client.list_conversations(page=page, status='all')
            conversations = data.get('data', {}).get('payload', [])
            meta = data.get('data', {}).get('meta', {})
            
            if not conversations:
                break
                
            for conv in conversations:
                conv_id = conv['id']
                # 1. Upsert Conversation
                try:
                    await upsert_conversation(session, conv)
                    
                    # 2. Fetch Messages
                    msgs_data = await client.get_messages(conv_id)
                    messages = msgs_data.get('payload', [])
                    for msg in messages:
                        await upsert_message(session, msg)
                        
                    # 3. Fetch Reporting Events (Conversation level)
                    # Note: API endpoint might not be exactly strictly documented for fetching ALL events per conv easily,
                    # but assumes implementation in client exists.
                    # As fallback, skipping if API returns 404.
                    try:
                        report_data = await client.get_conversation_reporting_events(conv_id)
                        # Assume report_data returns list of events
                        if isinstance(report_data, list):
                            await upsert_reporting_events(session, report_data)
                    except Exception as e:
                        logger.warning(f"Could not fetch reporting events for conv {conv_id}: {e}")

                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing conv {conv_id}: {e}")
            
            await session.commit()
            
            # Check pagination
            current_page = meta.get('current_page', page)
            total_pages = meta.get('total_pages', page)
            if current_page >= total_pages:
                break
            page += 1
            
        logger.info(f"Backfill Complete. Processed {processed_count} conversations.")

async def main():
    logger.info(f"Data Hub Runner Started. Interval: {settings.DATA_HUB_BACKFILL_INTERVAL_SECONDS}s")
    while True:
        try:
            await run_backfill()
        except Exception as e:
            logger.error(f"Backfill Job Failed: {e}")
        
        await asyncio.sleep(settings.DATA_HUB_BACKFILL_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())
