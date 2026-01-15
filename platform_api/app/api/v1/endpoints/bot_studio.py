from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.bot_studio import BotAgent, BotTask, BotCrew, BotCrewTaskLink, BotCrewVersion
from app.schemas import bot_studio as schemas

router = APIRouter()

# --- AGENTS ---
@router.post("/agents", response_model=schemas.BotAgent)
async def create_agent(agent: schemas.BotAgentCreate, db: AsyncSession = Depends(get_db)):
    db_agent = BotAgent(**agent.dict())
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    return db_agent

@router.get("/agents", response_model=List[schemas.BotAgent])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotAgent).order_by(BotAgent.id))
    return result.scalars().all()

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotAgent).where(BotAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
    return {"status": "deleted"}

# --- TASKS ---
@router.post("/tasks", response_model=schemas.BotTask)
async def create_task(task: schemas.BotTaskCreate, db: AsyncSession = Depends(get_db)):
    # Verify agent exists if provided
    if task.agent_id:
        res = await db.execute(select(BotAgent).where(BotAgent.id == task.agent_id))
        if not res.scalar_one_or_none():
             raise HTTPException(status_code=400, detail="Invalid Agent ID")

    db_task = BotTask(**task.dict())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.BotTask])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotTask).order_by(BotTask.id))
    return result.scalars().all()

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotTask).where(BotTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"status": "deleted"}

# --- CREWS ---
@router.post("/crews", response_model=schemas.BotCrew)
async def create_crew(crew: schemas.BotCrewCreate, db: AsyncSession = Depends(get_db)):
    db_crew = BotCrew(name=crew.name, description=crew.description, process=crew.process)
    db.add(db_crew)
    await db.commit()
    await db.refresh(db_crew)
    return db_crew

@router.post("/crews/{crew_id}/tasks")
async def link_tasks_to_crew(crew_id: int, links: List[schemas.TaskLinkCreate], db: AsyncSession = Depends(get_db)):
    """
    Overwrites existing links for this crew with the provided list.
    Effective way to reorder and update crew tasks.
    """
    # Verify Crew
    res = await db.execute(select(BotCrew).where(BotCrew.id == crew_id))
    db_crew = res.scalar_one_or_none()
    if not db_crew:
        raise HTTPException(status_code=404, detail="Crew not found")
        
    # Remove existing links
    await db.execute(select(BotCrewTaskLink).where(BotCrewTaskLink.crew_id == crew_id))
    # Note: Delete via ORM or simple delete statement. 
    # Proper way with cascade:
    # We query existing and delete them manually or use delete statement
    from sqlalchemy import delete
    await db.execute(delete(BotCrewTaskLink).where(BotCrewTaskLink.crew_id == crew_id))
    
    # Add new links
    for link in links:
        new_link = BotCrewTaskLink(crew_id=crew_id, task_id=link.task_id, step_order=link.step_order)
        db.add(new_link)
    
    await db.commit()
    return {"status": "updated", "count": len(links)}

@router.get("/crews/{crew_id}", response_model=schemas.BotCrewDetail)
async def get_crew(crew_id: int, db: AsyncSession = Depends(get_db)):
    # Eager load tasks via links AND versions
    stmt = (
        select(BotCrew)
        .options(
            selectinload(BotCrew.task_links).selectinload(BotCrewTaskLink.task),
            selectinload(BotCrew.versions)
        )
        .where(BotCrew.id == crew_id)
    )
    result = await db.execute(stmt)
    crew = result.scalar_one_or_none()
    
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
        
    # Sort tasks by step_order and flatten structure for response
    sorted_links = sorted(crew.task_links, key=lambda l: l.step_order)
    
    # Construct response object manual expansion
    response = schemas.BotCrewDetail.from_orm(crew)
    response.tasks = [link.task for link in sorted_links]
    
    return response

# --- PUBLISH / SNAPSHOT ---
@router.post("/crews/{crew_id}/publish", response_model=schemas.BotCrewVersion)
async def publish_crew(
    crew_id: int, 
    version_tag: str, 
    model_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an immutable snapshot of the crew configuration.
    Accepts optional model_id to bind a specific AI model to this version.
    """
    # Fetch full crew details
    stmt = (
        select(BotCrew)
        .options(
            selectinload(BotCrew.task_links).selectinload(BotCrewTaskLink.task).selectinload(BotTask.agent)
        )
        .where(BotCrew.id == crew_id)
    )
    result = await db.execute(stmt)
    crew = result.scalar_one_or_none()
    
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
        
    # Build Snapshot JSON
    sorted_links = sorted(crew.task_links, key=lambda l: l.step_order)
    
    tasks_snapshot = []
    agents_snapshot = []
    seen_agents = set()
    
    for link in sorted_links:
        task = link.task
        agent = task.agent
        
        task_data = {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "expected_output": task.expected_output,
            "agent_id": agent.id if agent else None
        }
        tasks_snapshot.append(task_data)
        
        if agent and agent.id not in seen_agents:
            agents_snapshot.append({
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "goal": agent.goal,
                "tools": agent.tools_json
            })
            seen_agents.add(agent.id)
            
    snapshot = {
        "crew": {
            "id": crew.id,
            "name": crew.name,
            "process": crew.process,
            "model_id": model_id # Saved in snapshot
        },
        "tasks": tasks_snapshot,
        "agents": agents_snapshot,
        "flow": [t["id"] for t in tasks_snapshot] # Order of execution by task ID
    }
    
    # Save Version
    version = BotCrewVersion(
        crew_id=crew.id,
        version_tag=version_tag,
        snapshot_json=snapshot
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    
    return version
