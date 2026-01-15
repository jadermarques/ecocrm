from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class BotAgent(Base):
    __tablename__ = "bot_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    tools_json = Column(JSON, default=list) # List of tool names or configs
    created_at = Column(datetime, default=datetime.utcnow)
    
    tasks = relationship("BotTask", back_populates="agent")

class BotTask(Base):
    __tablename__ = "bot_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    agent_id = Column(Integer, ForeignKey("bot_agents.id"), nullable=True)
    created_at = Column(datetime, default=datetime.utcnow)
    
    agent = relationship("BotAgent", back_populates="tasks")
    crew_links = relationship("BotCrewTaskLink", back_populates="task")

class BotCrew(Base):
    __tablename__ = "bot_crews"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    process = Column(String, default="sequential") # sequential, hierarchical
    created_at = Column(datetime, default=datetime.utcnow)
    
    task_links = relationship("BotCrewTaskLink", back_populates="crew", cascade="all, delete-orphan")
    versions = relationship("BotCrewVersion", back_populates="crew", cascade="all, delete-orphan")

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
    created_at = Column(datetime, default=datetime.utcnow)
    
    crew = relationship("BotCrew", back_populates="versions")
