from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base

class ChatwootWebhookEventRaw(Base):
    """
    Stores raw webhook events from Chatwoot for auditing and replay.
    """
    __tablename__ = "chatwoot_webhook_events_raw"

    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    event_name = Column(String, index=True, nullable=True)
    account_id = Column(Integer, nullable=True)
    conversation_id = Column(Integer, nullable=True)
    message_id = Column(Integer, nullable=True)
    
    payload_json = Column(JSONB, nullable=False)
    headers_json = Column(JSONB, nullable=True)
    
    is_valid = Column(Boolean, default=False)
    validation_error = Column(Text, nullable=True)
