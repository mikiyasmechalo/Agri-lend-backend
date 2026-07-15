from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class FarmerRegistrationHub(BaseModel):
    email: str
    password: str
    full_name: str
    national_id: str
    phone_number: str
    gps_coordinates: Optional[str] = None
    land_proof_document: Optional[str] = None
    crop_type: Optional[str] = None
    farm_size_hectares: Optional[Decimal] = None
    region: Optional[str] = None
    locale: str = "en"


class FarmerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    national_id: str
    phone_number: str
    mobile_money_id: Optional[str]
    gps_coordinates: Optional[str]
    land_proof_document: Optional[str]
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


class ConsentRequest(BaseModel):
    consent: bool


class ExplainabilityResponse(BaseModel):
    farmer_id: UUID
    score_value: int
    risk_tier: str
    summary: str
    top_factors: list[dict]


class FarmStatusResponse(BaseModel):
    farmer_id: UUID
    ndvi_current: Optional[float]
    ndvi_trend: list[dict]
    crop_health_label: str
