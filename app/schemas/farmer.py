from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class FarmerProfileCreate(BaseModel):
    user_id: UUID
    national_id: str
    phone_number: str
    mobile_money_id: Optional[str] = None
    locale: str = "en"


class FarmerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    national_id: str
    phone_number: str
    mobile_money_id: Optional[str]
    consent_status: bool
    consent_date: Optional[datetime]
    locale: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmParcelCreate(BaseModel):
    farmer_id: UUID
    parcel_name: str
    size_hectares: Decimal
    primary_crop: str
    region: str


class FarmParcelResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    parcel_name: str
    size_hectares: Decimal
    primary_crop: str
    region: str
    created_at: datetime

    model_config = {"from_attributes": True}
