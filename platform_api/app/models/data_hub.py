from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base

class RawChatwootEvent(Base):
    """
    Stores all incoming Chatwoot Webhook events in their raw format.
    Consolidates previous ChatwootWebhookEventRaw.
    """
    __tablename__ = "raw_chatwoot_events"

    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    event_name = Column(String, index=True, nullable=True)
    account_id = Column(Integer, nullable=True)
    inbox_id = Column(Integer, nullable=True)
    conversation_id = Column(Integer, nullable=True)
    message_id = Column(Integer, nullable=True)
    
    payload_json = Column(JSONB, nullable=False)
    headers_json = Column(JSONB, nullable=True)
    
    is_valid = Column(Boolean, default=False)
    validation_error = Column(Text, nullable=True)


class RawChatwootConversation(Base):
    """
    Mirror of Chatwoot Conversations.
    """
    __tablename__ = "raw_chatwoot_conversations"

    # Using Integer might refer to Chatwoot ID. 
    # Chatwoot IDs are ints, but let's use BigInteger to be safe or Integer if standard.
    conversation_id = Column(Integer, primary_key=True)
    
    account_id = Column(Integer, nullable=False)
    inbox_id = Column(Integer, nullable=False)
    status = Column(String, nullable=True)
    assignee_id = Column(Integer, nullable=True)
    contact_id = Column(Integer, nullable=True)
    
    created_at_ts = Column(DateTime, nullable=True)
    updated_at_ts = Column(DateTime, nullable=True)
    
    payload_json = Column(JSONB, nullable=True) # Full raw object


class RawChatwootMessage(Base):
    """
    Mirror of Chatwoot Messages.
    """
    __tablename__ = "raw_chatwoot_messages"

    message_id = Column(Integer, primary_key=True)
    
    conversation_id = Column(Integer, nullable=False)
    account_id = Column(Integer, nullable=False)
    inbox_id = Column(Integer, nullable=False)
    
    message_type = Column(Integer, nullable=True) # 0=incoming, 1=outgoing
    content = Column(Text, nullable=True)
    private = Column(Boolean, default=False)
    
    sender_type = Column(String, nullable=True) # Contact, User, etc
    sender_id = Column(Integer, nullable=True)
    
    created_at_ts = Column(DateTime, nullable=True)
    updated_at_ts = Column(DateTime, nullable=True)
    
    payload_json = Column(JSONB, nullable=True)


class RawChatwootReportingEvent(Base):
    """
    Mirror of Reporting Events from Chatwoot APIs.
    """
    __tablename__ = "raw_chatwoot_reporting_events"

    reporting_event_id = Column(BigInteger, primary_key=True) # Chatwoot reporting events IDs might be large
    
    account_id = Column(Integer, nullable=False)
    conversation_id = Column(Integer, nullable=True)
    inbox_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    
    name = Column(String, nullable=True) # first_response, etc
    value_seconds = Column(Integer, nullable=True)
    value_business_hours_seconds = Column(Integer, nullable=True)
    
    event_start_time = Column(DateTime, nullable=True)
    event_end_time = Column(DateTime, nullable=True)
    
    created_at_ts = Column(DateTime, nullable=True)
    updated_at_ts = Column(DateTime, nullable=True)
    
    payload_json = Column(JSONB, nullable=True)
