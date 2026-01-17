from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class BotRun(Base):
    __tablename__ = "bot_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) # UUID string
    crew_version_id = Column(ForeignKey("bot_crew_versions.id"), nullable=True) # Nullable for ad-hoc/test runs
    source = Column(String, default="manual") # chatwoot, manual
    conversation_id = Column(String, nullable=True) # Chatwoot conversation ID or TestLab run_id
    status = Column(String, default="running") # running, success, failed
    result_output = Column(Text, nullable=True) # Final Answer
    
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    events = relationship("BotRunEvent", back_populates="run", cascade="all, delete-orphan")
    crew_version = relationship("app.models.bot_studio.BotCrewVersion")

class BotRunEvent(Base):
    __tablename__ = "bot_run_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(ForeignKey("bot_runs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, nullable=False) # task_start, task_end, error, final_answer
    payload_json = Column(JSONB, default={})
    
    run = relationship("BotRun", back_populates="events")
