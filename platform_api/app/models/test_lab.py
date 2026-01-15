from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, FetchedValue
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class TestRun(Base):
    id = Column(String, primary_key=True, index=True) # UUID provided by client or generated
    name = Column(String, nullable=True)
    persona = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    events = relationship("TestRunEvent", back_populates="run", cascade="all, delete-orphan")

class TestRunEvent(Base):
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("testrun.id"), nullable=False)
    role = Column(String, nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    run = relationship("TestRun", back_populates="events")
