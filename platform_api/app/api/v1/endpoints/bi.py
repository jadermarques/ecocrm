from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()

@router.get("/volume")
async def get_volume(
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
    inbox_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Daily volume of conversations and messages."""
    params = {"d_from": date_from, "d_to": date_to}
    query = """
        SELECT day, inbox_id, conversations_count, messages_count
        FROM mart_inbox_daily_volume
        WHERE day >= :d_from AND day <= :d_to
    """
    if inbox_id:
        query += " AND inbox_id = :inbox_id"
        params["inbox_id"] = inbox_id
    
    query += " ORDER BY day ASC"
    
    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result]

@router.get("/agent-volume")
async def get_agent_volume(
    date_from: str = Query(...),
    date_to: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Ranking of agents by volume."""
    # Aggregating daily stats over the period
    query = """
        SELECT user_id, SUM(messages_count) as total_messages, SUM(conversations_touched) as total_conversations
        FROM mart_agent_daily_volume
        WHERE day >= :d_from AND day <= :d_to
        GROUP BY user_id
        ORDER BY total_messages DESC
    """
    result = await db.execute(text(query), {"d_from": date_from, "d_to": date_to})
    return [dict(row._mapping) for row in result]

@router.get("/time-metrics")
async def get_time_metrics(
    date_from: str = Query(None), # Not always applicable if mart is lifetime, assuming mart is per conversation
    # Conversations don't have a rigid 'date' in the mart unless looking at creation date in stg joined?
    # The mart_conversation_time_metrics is keyed by conversation_id. 
    # To filter by date, we need to join stg_conversations or add date to mart.
    # I'll join stg_conversations for filtering.
    date_to: str = Query(None),
    inbox_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    SLA Metrics: First Response, Resolution, etc.
    Returns aggregates (AVG, P50, P90).
    """
    query = """
    WITH filtered AS (
        SELECT 
            m.first_response_seconds,
            m.resolution_seconds,
            m.reply_time_seconds
        FROM mart_conversation_time_metrics m
        JOIN stg_conversations c ON c.conversation_id = m.conversation_id
        WHERE 1=1
    """
    params = {}
    if date_from:
        query += " AND c.created_at >= :d_from"
        params["d_from"] = date_from
    if date_to:
        query += " AND c.created_at <= :d_to"
        params["d_to"] = date_to
    if inbox_id:
        query += " AND m.inbox_id = :inbox_id"
        params["inbox_id"] = inbox_id
    
    query += """)
    SELECT
        AVG(first_response_seconds) as avg_first_response,
        PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY first_response_seconds) as p50_first_response,
        PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY first_response_seconds) as p90_first_response,
        
        AVG(resolution_seconds) as avg_resolution,
        PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY resolution_seconds) as p50_resolution,
        
        AVG(reply_time_seconds) as avg_reply_time
    FROM filtered
    """
    
    result = await db.execute(text(query), params)
    row = result.fetchone()
    return dict(row._mapping) if row else {}

@router.get("/backlog")
async def get_backlog(
    inbox_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Latest backlog snapshot."""
    # Get latest snapshot timestamp
    query_ts = "SELECT MAX(snapshot_ts) FROM mart_backlog_snapshot"
    ts_res = await db.execute(text(query_ts))
    latest_ts = ts_res.scalar()
    
    if not latest_ts:
        return []
    
    query = """
        SELECT inbox_id, status, count
        FROM mart_backlog_snapshot
        WHERE snapshot_ts = :ts
    """
    params = {"ts": latest_ts}
    if inbox_id:
        query += " AND inbox_id = :inbox_id"
        params["inbox_id"] = inbox_id
        
    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result]
