from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.kb import FileStatus

class KBFileBase(BaseModel):
    filename: str
    status: FileStatus
    usage_bytes: Optional[int] = None

class KBFile(KBFileBase):
    id: int
    kb_id: int
    openai_file_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    expires_after_days: Optional[int] = None

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBase(KnowledgeBaseBase):
    id: int
    openai_vector_store_id: Optional[str]
    created_at: datetime
    files: List[KBFile] = []
    class Config:
        from_attributes = True
