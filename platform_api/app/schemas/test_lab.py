from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel
from pydantic.types import Json

class TestRunEventBase(BaseModel):
    event_type: str
    payload_json: Any
    
class TestRunEvent(TestRunEventBase):
    id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class TestRunBase(BaseModel):
    source: str = "manual"
    status: str = "running"

class TestRunCreate(TestRunBase):
    id: str
    crew_version_id: Optional[int] = None # Optional override

class TestRun(TestRunBase):
    id: str
    created_at: datetime
    finished_at: Optional[datetime]
    result_output: Optional[str]
    events: List[TestRunEvent] = []
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str
    role: str = "user"
    crew_version_id: Optional[int] = None
