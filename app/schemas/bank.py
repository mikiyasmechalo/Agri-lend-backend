from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class BankPartnerCreate(BaseModel):
    bank_name: str
    subscription_tier: str = "standard"


class BankPartnerResponse(BaseModel):
    id: UUID
    bank_name: str
    subscription_tier: str
    is_active: bool
    onboarding_date: datetime

    model_config = {"from_attributes": True}


class BankSettingsUpdate(BaseModel):
    bank_name: Optional[str] = None
    subscription_tier: Optional[str] = None
