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

@router.put("/agents/{agent_id}", response_model=schemas.BotAgent)
async def update_agent(agent_id: int, agent_update: schemas.BotAgentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotAgent).where(BotAgent.id == agent_id))
    db_agent = result.scalar_one_or_none()
    
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)
        
    await db.commit()
    await db.refresh(db_agent)
    return db_agent

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

@router.put("/tasks/{task_id}", response_model=schemas.BotTask)
async def update_task(task_id: int, task_update: schemas.BotTaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotTask).where(BotTask.id == task_id))
    db_task = result.scalar_one_or_none()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Verify agent exists if provided
    if task_update.agent_id is not None:
        agent_res = await db.execute(select(BotAgent).where(BotAgent.id == task_update.agent_id))
        if not agent_res.scalar_one_or_none():
             raise HTTPException(status_code=400, detail="Invalid Agent ID")

    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    await db.commit()
    await db.refresh(db_task)
    return db_task

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
    await db.refresh(db_crew)
    return db_crew

@router.get("/crews", response_model=List[schemas.BotCrew])
async def list_crews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotCrew).order_by(BotCrew.id))
    return result.scalars().all()

@router.put("/crews/{crew_id}", response_model=schemas.BotCrew)
async def update_crew(crew_id: int, crew_update: schemas.BotCrewUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotCrew).where(BotCrew.id == crew_id))
    db_crew = result.scalar_one_or_none()
    
    if not db_crew:
        raise HTTPException(status_code=404, detail="Crew not found")
        
    update_data = crew_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_crew, key, value)
        
    await db.commit()
    await db.refresh(db_crew)
    await db.refresh(db_crew)
    return db_crew

@router.delete("/crews/{crew_id}")
async def delete_crew(crew_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BotCrew).where(BotCrew.id == crew_id))
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
        
    # Check if we should delete tasks or just links?
    # For now just delete crew, which cascades to links if configured or needs manual link deletion
    # We manually delete links first
    from sqlalchemy import delete
    await db.execute(delete(BotCrewTaskLink).where(BotCrewTaskLink.crew_id == crew_id))
    
    # Also delete versions?
    await db.execute(delete(BotCrewVersion).where(BotCrewVersion.crew_id == crew_id))
    
    await db.delete(crew)
    await db.commit()
    return {"status": "deleted"}

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
    # Use model_validate for Pydantic V2 compat
    response = schemas.BotCrewDetail.model_validate(crew)
    
    # Convert SQLAlchemy objects to Pydantic models explicitly
    response.tasks = [schemas.BotTask.model_validate(link.task) for link in sorted_links]
    
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
            "agent_id": agent.id if agent else None,
            "async_execution": task.async_execution,
            "context_task_ids": task.context_task_ids,
            "tools": task.tools_json,
            # capture other potential fields if added to model later
        }
        tasks_snapshot.append(task_data)
        
        if agent and agent.id not in seen_agents:
            agents_snapshot.append({
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory,
                "tools": agent.tools_json,
                "llm": agent.llm,
                "function_calling_llm": agent.function_calling_llm,
                "allow_delegation": agent.allow_delegation,
                "verbose": agent.verbose,
                "max_iter": agent.max_iter,
                "max_rpm": agent.max_rpm,
                "max_execution_time": agent.max_execution_time,
                "knowledge_sources": agent.knowledge_sources
            })
            seen_agents.add(agent.id)
            
    snapshot = {
        "crew": {
            "id": crew.id,
            "name": crew.name,
            "process": crew.process,
            "manager_llm": crew.manager_llm,
            "function_calling_llm": crew.function_calling_llm,
            "verbose": crew.verbose,
            "max_rpm": crew.max_rpm,
            "manager_agent_id": crew.manager_agent_id,
            "memory_enabled": crew.memory_enabled,
            "config": crew.config_json,
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
