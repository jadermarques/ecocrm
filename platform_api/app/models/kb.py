from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class FileStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    strategy = Column(String, default="openai_vector_store")
    openai_vector_store_id = Column(String, nullable=True) # The VS ID on OpenAI side
    
    expires_after_days = Column(Integer, nullable=True) # For cost control
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("KBFile", back_populates="kb", cascade="all, delete-orphan")

class KBFile(Base):
    __tablename__ = "kb_files"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    
    openai_file_id = Column(String, nullable=True) # Metadata file ID
    openai_vector_store_file_id = Column(String, nullable=True) # Link ID in VS
    
    # Local storage fields (when not using OpenAI)
    local_file_path = Column(String, nullable=True) # Path to file in /app/data/kb_files/
    file_content = Column(Text, nullable=True) # Text content extracted (for search)
    
    status = Column(Enum(FileStatus), default=FileStatus.in_progress)
    usage_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    kb = relationship("KnowledgeBase", back_populates="files")
