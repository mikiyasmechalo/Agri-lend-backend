from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.credit import RiskTier


class CreditScoreResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    score_value: int
    risk_tier: RiskTier
    model_version: str
    confidence_rating: Decimal
    calculated_at: datetime

    model_config = {"from_attributes": True}


class CreditScoreHistoryResponse(BaseModel):
    items: list[CreditScoreResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    trend: str


class ExplainabilityResponse(BaseModel):
    farmer_id: UUID
    score_value: int
    risk_tier: str
    summary: str
    top_factors: list[dict]
