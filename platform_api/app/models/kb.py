from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base

class KBDocument(Base):
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    content_type = Column(String, nullable=True)
    file_path = Column(String, nullable=False) # Path inside container
    upload_ip = Column(String, nullable=True)
    processed = Column(Boolean(), default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
