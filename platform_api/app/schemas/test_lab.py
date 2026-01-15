from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class TestRunEventBase(BaseModel):
    role: str
    content: str
    
class TestRunEventCreate(TestRunEventBase):
    pass

class TestRunEvent(TestRunEventBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TestRunBase(BaseModel):
    name: Optional[str] = None
    persona: Optional[str] = None

class TestRunCreate(TestRunBase):
    id: str

class TestRun(TestRunBase):
    id: str
    created_at: datetime
    events: List[TestRunEvent] = []
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str
    role: str = "user"
