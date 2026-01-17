from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import asyncio

from app.db.session import get_db
from app.models.bot_run import BotRun, BotRunEvent
from app.models.bot_studio import BotCrewVersion
from app.schemas.test_lab import TestRunCreate, TestRun as TestRunSchema, TestRunEvent as TestRunEventSchema, MessageCreate
from app.core.config import settings

router = APIRouter()

# Helper (Should be shared but implemented here for speed/MVP as per strict separation usually desired)
import logging
import json
from pathlib import Path
from langchain.callbacks.base import BaseCallbackHandler
from typing import Optional

from shared.libs.crew_execution import execute_crew_from_snapshot

# AGENT Templates and logging handlers moved to shared.libs.crew_execution to share with bot_runner


@router.post("/runs", response_model=TestRunSchema)
async def create_test_run(
    run_in: TestRunCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new manual run context."""
    # Check if exists
    result = await db.execute(select(BotRun).where(BotRun.id == run_in.id))
    existing = result.scalars().first()
    if existing:
        return existing
        
    db_obj = BotRun(
        id=run_in.id, 
        source="manual", 
        status="running"
        # crew_version_id intentionally left null initially or set if provided
    )
    if run_in.crew_version_id:
        db_obj.crew_version_id = run_in.crew_version_id
        
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/runs/{run_id}", response_model=TestRunSchema)
async def get_test_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific run."""
    result = await db.execute(
        select(BotRun).where(BotRun.id == run_id).options(selectinload(BotRun.events))
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.post("/runs/{run_id}/messages", response_model=TestRunEventSchema)
async def add_message(
    run_id: str,
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Submits a message to the run.
    This triggers the pipeline execution synchronously for the Test Lab MVP.
    """
    # 1. Get Run
    result = await db.execute(select(BotRun).where(BotRun.id == run_id))
    run = result.scalars().first()
    if not run:
        # Auto-create
        run = BotRun(id=run_id, source="manual", status="running")
        db.add(run)
        await db.commit()
    
    # 2. Log User Message
    user_event = BotRunEvent(
        run_id=run.id,
        event_type="user_message",
        payload_json={"content": msg_in.content, "role": msg_in.role}
    )
    db.add(user_event)
    await db.commit()
    
    # 3. Determine Crew Version
    version_id = msg_in.crew_version_id or run.crew_version_id 
    # Fallback to default if not set in run (MVP: use env default if run has none)
    if not version_id:
         # Need to fetch default from settings or simple query
         # We'll use a hardcoded fallback or Env if available in config object
         # Assuming consumer settings aren't directly available here, query latest or v1
         # For safety, let's query first available
         v_res = await db.execute(select(BotCrewVersion).order_by(BotCrewVersion.id.desc()).limit(1))
         v = v_res.scalars().first()
         if v:
             version_id = v.id
         else:
             # Skip execution, just echo
             pass
    
    # 4. Execute Pipeline (Sync for MVP feedback in UI)
    bot_reply_content = "No crew version available."
    agent_name = "Sistema"
    
    if version_id:
        v_res = await db.execute(select(BotCrewVersion).where(BotCrewVersion.id == version_id))
        version = v_res.scalars().one_or_none()
        if version:
            run.crew_version_id = version.id
            
            # Exec
            result_dict = await execute_crew_from_snapshot(
                version.snapshot_json, 
                {"content": msg_in.content},
                version_tag=version.version_tag
            )
            
            if isinstance(result_dict, dict):
                bot_reply_content = result_dict.get("response", str(result_dict))
                agent_name = result_dict.get("agent_name", "Agente")
            else:
                bot_reply_content = str(result_dict)
                agent_name = "Agente"
    
    # 5. Log Bot Response with agent name
    bot_event = BotRunEvent(
        run_id=run.id,
        event_type="bot_message",
        payload_json={
            "content": bot_reply_content, 
            "role": "assistant",
            "agent_name": agent_name
        }
    )
    db.add(bot_event)
    await db.commit()
    await db.refresh(bot_event)
    
    return bot_event

@router.get("/runs/{run_id}/events", response_model=List[TestRunEventSchema])
async def get_run_events(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    result = await db.execute(
        select(BotRunEvent).where(BotRunEvent.run_id == run_id).order_by(BotRunEvent.timestamp)
    )
    return result.scalars().all()

@router.get("/runs/{run_id}/events/stream")
async def stream_run_events(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events (SSE) for real-time run monitoring.
    Polls DB for new events.
    """
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        last_event_time = None
        import json
        
        # Keep connection open for a while or until run finishes
        for _ in range(60): 
            # Check for new events
            query = select(BotRunEvent).where(BotRunEvent.run_id == run_id)
            if last_event_time:
                query = query.where(BotRunEvent.timestamp > last_event_time)
            query = query.order_by(BotRunEvent.timestamp)
            
            result = await db.execute(query)
            new_events = result.scalars().all()
            
            for event in new_events:
                data = {
                    "id": event.id,
                    "type": event.event_type,
                    "payload": event.payload_json,
                    "ts": event.timestamp.isoformat()
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_event_time = event.timestamp
            
            await asyncio.sleep(1)
            
            # Check run status
            r_res = await db.execute(select(BotRun).where(BotRun.id == run_id))
            r = r_res.scalars().first()
            if r and r.status in ["success", "failed"]:
                yield f"data: {{\"type\": \"status_change\", \"status\": \"{r.status}\"}}\n\n"
                break
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")
