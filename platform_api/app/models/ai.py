from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Numeric, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class AiProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True) # e.g. OpenAI
    base_url = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    models = relationship("AiModel", back_populates="provider", cascade="all, delete-orphan")

class AiModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=False)
    name = Column(String, nullable=False) # e.g. gpt-4-turbo
    modality = Column(String, default="text") # text, embeddings
    
    # Costs per 1M tokens
    input_cost_per_1m = Column(Numeric(10, 4), default=0)
    output_cost_per_1m = Column(Numeric(10, 4), default=0)
    cached_input_cost_per_1m = Column(Numeric(10, 4), nullable=True)
    
    currency = Column(String, default="USD")
    
    # Limits
    context_window_tokens = Column(Integer, nullable=True)
    max_output_tokens = Column(Integer, nullable=True)
    rpm_limit = Column(Integer, nullable=True)
    tpm_limit = Column(Integer, nullable=True)
    
    is_default = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("AiProvider", back_populates="models")

class AiUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, nullable=True, index=True) # Link to BotRun if needed
    
    provider_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    estimated_cost = Column(Numeric(10, 6), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
