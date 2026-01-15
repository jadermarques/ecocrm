from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# --- Agent Schemas ---
class BotAgentBase(BaseModel):
    name: str
    role: str
    goal: str
    tools_json: Optional[List[str]] = []

class BotAgentCreate(BotAgentBase):
    pass

class BotAgentUpdate(BotAgentBase):
    pass

class BotAgent(BotAgentBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Task Schemas ---
class BotTaskBase(BaseModel):
    name: str
    description: str
    expected_output: Optional[str] = None
    agent_id: Optional[int] = None

class BotTaskCreate(BotTaskBase):
    pass

class BotTaskUpdate(BotTaskBase):
    pass

class BotTask(BotTaskBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Layout/Link Helper ---
class TaskLinkCreate(BaseModel):
    task_id: int
    step_order: int

# --- Crew Schemas ---
class BotCrewBase(BaseModel):
    name: str
    description: Optional[str] = None
    process: Optional[str] = "sequential"

class BotCrewCreate(BotCrewBase):
    # Optional: Initial tasks can be passed
    initial_tasks: Optional[List[TaskLinkCreate]] = None

class BotCrewUpdate(BotCrewBase):
    pass

class BotCrew(BotCrewBase):
    id: int
    created_at: datetime
    # We might want to return linked tasks, but keep it simple for now
    class Config:
        from_attributes = True

class BotCrewDetail(BotCrew):
    """Crew details with linked tasks expanded."""
    tasks: List[Any] = [] # Will hold Ordered Task objects
    versions: List[BotCrewVersion] = []

# --- Version Schemas ---
class BotCrewVersionBase(BaseModel):
    version_tag: str

class BotCrewVersion(BotCrewVersionBase):
    id: int
    crew_id: int
    created_at: datetime
    snapshot_json: Any
    class Config:
        from_attributes = True
