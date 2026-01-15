import logging
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger("Analytics")

INIT_SQL_PATH = "platform_api/app/db/analytics.sql"

async def init_analytics_schema(session):
    """Reads SQL file and executes it to create Views/Tables if not exist"""
    try:
        with open(INIT_SQL_PATH, "r") as f:
            sql_script = f.read()
        
        # Split by command if necessary or execute block
        # SQLAlchemy execute text handles basic blocks usually
        await session.execute(text(sql_script))
        await session.commit()
        logger.info("Analytics Schema Initialized.")
    except Exception as e:
        logger.error(f"Failed to init analytics schema: {e}")
        # Not raising, as it might be 'already exists' or syntax error we want to log but not crash worker loop
        # Ideally we handle specific errors.

async def refresh_marts(session):
    """Refreshes Materialized Views and Takes Snapshots"""
    logger.info("Refreshing Analytics Marts...")
    
    try:
        # Refresh Materialized Views
        await session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mart_inbox_daily_volume"))
        await session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mart_agent_daily_volume"))
        await session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mart_conversation_time_metrics"))
        
        # Snapshot Backlog
        # We group by inbox and status from STG_CONVERSATIONS
        snapshot_sql = """
        INSERT INTO mart_backlog_snapshot (snapshot_ts, inbox_id, status, count)
        SELECT NOW(), inbox_id, status, COUNT(*)
        FROM stg_conversations
        WHERE status IN ('open', 'pending', 'snoozed', 'resolved')
        GROUP BY inbox_id, status;
        """
        await session.execute(text(snapshot_sql))
        
        await session.commit()
        logger.info("Analytics Marts Refreshed.")
        
    except Exception as e:
        logger.error(f"Error refreshing marts: {e}")
        # Note: XML/Concurrent refresh might fail if not populated first.
        # If 'concurrently' fails (first run), try without.
        if "without data" in str(e).lower() or "concurrently" in str(e).lower():
            try:
                await session.execute(text("REFRESH MATERIALIZED VIEW mart_inbox_daily_volume"))
                await session.execute(text("REFRESH MATERIALIZED VIEW mart_agent_daily_volume"))
                await session.execute(text("REFRESH MATERIALIZED VIEW mart_conversation_time_metrics"))
                await session.commit()
                logger.info("Analytics Marts Refreshed (Non-Concurrent).")
            except Exception as e2:
                 logger.error(f"Retry refresh failed: {e2}")
