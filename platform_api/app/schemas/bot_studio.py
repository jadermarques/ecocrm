from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# --- Agent Schemas ---
class BotAgentBase(BaseModel):
    name: str
    role: str
    goal: str
    backstory: Optional[str] = None
    tools_json: Optional[List[str]] = []
    
    # LLM Configuration
    llm: Optional[str] = None
    function_calling_llm: Optional[str] = None
    
    # Execution Control
    max_iter: Optional[int] = 20
    max_rpm: Optional[int] = None
    max_execution_time: Optional[int] = None
    
    # Behavior Flags
    verbose: Optional[bool] = False
    allow_delegation: Optional[bool] = False
    reasoning: Optional[bool] = False
    
    # Knowledge
    knowledge_sources: Optional[List[Any]] = None

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
    
    # Task-specific configuration
    tools_json: Optional[List[str]] = None
    context_task_ids: Optional[List[int]] = None
    
    # Execution Settings
    async_execution: Optional[bool] = False
    
    # Output Configuration
    output_json_schema: Optional[Any] = None
    output_pydantic_schema: Optional[Any] = None
    
    # Callbacks and Guardrails
    callback_config: Optional[Any] = None
    guardrail_config: Optional[Any] = None
    guardrail_max_retries: Optional[int] = 3

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
    
    # Execution Configuration
    verbose: Optional[bool] = False
    max_rpm: Optional[int] = None
    
    # LLM Configuration
    manager_llm: Optional[str] = None
    function_calling_llm: Optional[str] = None
    
    # Manager Configuration
    manager_agent_id: Optional[int] = None
    
    # Advanced Features
    config_json: Optional[Any] = None
    memory_enabled: Optional[bool] = False
    knowledge_sources: Optional[List[Any]] = None
    
    # Callbacks and Logging
    step_callback_config: Optional[Any] = None
    task_callback_config: Optional[Any] = None
    output_log_file: Optional[str] = None
    
    # Sharing
    share_crew: Optional[bool] = False

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

# --- Link Schema for Response ---
class LinkSchema(BaseModel):
    task_id: int
    step_order: int
    class Config:
        from_attributes = True

class BotCrewDetail(BotCrew):
    """Crew details with linked tasks expanded."""
    tasks: List[Any] = [] # Will hold Ordered Task objects
    versions: List[BotCrewVersion] = []
    
    # helper for UI to know current links
    task_links: List[LinkSchema] = []
