from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class BotAgent(Base):
    __tablename__ = "bot_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    backstory = Column(Text, nullable=True)
    tools_json = Column(JSON, default=list) # List of tool names or configs
    
    # LLM Configuration
    llm = Column(String, nullable=True)  # Model name or config
    function_calling_llm = Column(String, nullable=True)
    
    # Execution Control
    max_iter = Column(Integer, default=20)
    max_rpm = Column(Integer, nullable=True)
    max_execution_time = Column(Integer, nullable=True)
    
    # Behavior Flags
    verbose = Column(Boolean, default=False)
    allow_delegation = Column(Boolean, default=False)
    reasoning = Column(Boolean, default=False)
    
    # Knowledge
    knowledge_sources = Column(JSON, nullable=True)  # List of knowledge source configs
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("BotTask", back_populates="agent")

class BotTask(Base):
    __tablename__ = "bot_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    agent_id = Column(Integer, ForeignKey("bot_agents.id"), nullable=True)
    
    # Task-specific configuration
    tools_json = Column(JSON, nullable=True)  # List of tool names for this specific task
    context_task_ids = Column(JSON, nullable=True)  # List of task IDs to use as context
    
    # Execution Settings
    async_execution = Column(Boolean, default=False)
    
    # Output Configuration
    output_json_schema = Column(JSON, nullable=True)  # Pydantic model schema
    output_pydantic_schema = Column(JSON, nullable=True)  # Alternative output schema
    
    # Callbacks and Guardrails
    callback_config = Column(JSON, nullable=True)  # Callback function config
    guardrail_config = Column(JSON, nullable=True)  # Guardrail validation function config
    guardrail_max_retries = Column(Integer, default=3)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("BotAgent", back_populates="tasks")
    crew_links = relationship("BotCrewTaskLink", back_populates="task")

class BotCrew(Base):
    __tablename__ = "bot_crews"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    process = Column(String, default="sequential") # sequential, hierarchical
    
    # Execution Configuration
    verbose = Column(Boolean, default=False)
    max_rpm = Column(Integer, nullable=True)
    
    # LLM Configuration
    manager_llm = Column(String, nullable=True)  # Required for hierarchical process
    function_calling_llm = Column(String, nullable=True)
    
    # Manager Configuration
    manager_agent_id = Column(Integer, ForeignKey("bot_agents.id"), nullable=True)  # Custom manager agent
    
    # Advanced Features
    config_json = Column(JSON, nullable=True)  # Additional crew configuration
    memory_enabled = Column(Boolean, default=False)  # Enable short/long-term memory
    knowledge_sources = Column(JSON, nullable=True)  # Crew-level knowledge sources
    
    # Callbacks and Logging
    step_callback_config = Column(JSON, nullable=True)
    task_callback_config = Column(JSON, nullable=True)
    output_log_file = Column(String, nullable=True)  # Path to log file
    
    # Sharing
    share_crew = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task_links = relationship("BotCrewTaskLink", back_populates="crew", cascade="all, delete-orphan")
    versions = relationship("BotCrewVersion", back_populates="crew", cascade="all, delete-orphan")
    manager_agent = relationship("BotAgent", foreign_keys=[manager_agent_id])

class BotCrewTaskLink(Base):
    """Link table to order tasks within a crew."""
    __tablename__ = "bot_crew_task_links"
    
    id = Column(Integer, primary_key=True, index=True)
    crew_id = Column(Integer, ForeignKey("bot_crews.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("bot_tasks.id"), nullable=False)
    step_order = Column(Integer, nullable=False, default=0) # Order of execution
    
    crew = relationship("BotCrew", back_populates="task_links")
    task = relationship("BotTask", back_populates="crew_links")

class BotCrewVersion(Base):
    """Immutable snapshot of a crew configuration."""
    __tablename__ = "bot_crew_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    crew_id = Column(Integer, ForeignKey("bot_crews.id"), nullable=False)
    version_tag = Column(String, nullable=False) # e.g., "v1.0"
    snapshot_json = Column(JSON, nullable=False) # Full JSON dump of crew+agents+tasks
    created_at = Column(DateTime, default=datetime.utcnow)
    
    crew = relationship("BotCrew", back_populates="versions")
