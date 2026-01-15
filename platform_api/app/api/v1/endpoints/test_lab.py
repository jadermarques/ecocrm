from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.test_lab import TestRun, TestRunEvent
from app.schemas.test_lab import TestRunCreate, TestRun as TestRunSchema, TestRunEvent as TestRunEventSchema, MessageCreate

router = APIRouter()

@router.post("/runs", response_model=TestRunSchema)
async def create_test_run(
    run_in: TestRunCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new test run for the Test Lab."""
    # Check if exists
    result = await db.execute(select(TestRun).where(TestRun.id == run_in.id))
    existing = result.scalars().first()
    if existing:
        return existing
        
    db_obj = TestRun(id=run_in.id, name=run_in.name, persona=run_in.persona)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/runs/{run_id}", response_model=TestRunSchema)
async def get_test_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific test run by ID."""
    result = await db.execute(
        select(TestRun).where(TestRun.id == run_id).options(selectinload(TestRun.events))
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
    """Add a message to the test run (User or System)."""
    # Verify run exists
    result = await db.execute(select(TestRun).where(TestRun.id == run_id))
    run = result.scalars().first()
    if not run:
        # Auto-create if not exists for simpler UX in prototype
        run = TestRun(id=run_id, name="Auto Created")
        db.add(run)
        await db.commit()
    
    event = TestRunEvent(
        run_id=run_id,
        role=msg_in.role,
        content=msg_in.content
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # In a real scenario, this is where we would trigger the Bot Runner?
    # Or the frontend triggers it separately.
    
    return event

@router.get("/runs/{run_id}/events", response_model=List[TestRunEventSchema])
async def get_run_events(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all events for a specific test run."""
    result = await db.execute(
        select(TestRunEvent).where(TestRunEvent.run_id == run_id).order_by(TestRunEvent.created_at)
    )
    return result.scalars().all()
