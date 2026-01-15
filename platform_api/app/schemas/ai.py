from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal

# --- Provider ---
class AiProviderBase(BaseModel):
    name: str
    base_url: Optional[str] = None
    is_enabled: bool = True
    notes: Optional[str] = None

class AiProviderCreate(AiProviderBase):
    pass

class AiProviderUpdate(AiProviderBase):
    pass

class AiProvider(AiProviderBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Model ---
class AiModelBase(BaseModel):
    name: str # The technical model name passed to the API
    modality: str = "text"
    input_cost_per_1m: Decimal = 0
    output_cost_per_1m: Decimal = 0
    cached_input_cost_per_1m: Optional[Decimal] = None
    currency: str = "USD"
    context_window_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    rpm_limit: Optional[int] = None
    tpm_limit: Optional[int] = None
    is_default: bool = False
    is_enabled: bool = True

class AiModelCreate(AiModelBase):
    provider_id: int

class AiModelUpdate(AiModelBase):
    provider_id: Optional[int] = None

class AiModel(AiModelBase):
    id: int
    provider_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class AiModelDetail(AiModel):
    provider: Optional[AiProvider] = None

# --- Usage Log ---
class AiUsageLogBase(BaseModel):
    run_id: Optional[str] = None
    provider_name: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: Decimal

class AiUsageLogCreate(AiUsageLogBase):
    pass

class AiUsageLog(AiUsageLogBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True
