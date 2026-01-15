from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class KBDocumentBase(BaseModel):
    filename: str
    content_type: Optional[str] = None
    processed: bool = False

class KBDocument(KBDocumentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
