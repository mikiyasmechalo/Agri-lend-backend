from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.loan import LoanStatus


class LoanApplicationCreate(BaseModel):
    farmer_id: UUID
    bank_id: UUID
    requested_amount: Decimal
    loan_purpose: str


class LoanApplicationResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    bank_id: UUID
    requested_amount: Decimal
    loan_purpose: str
    credit_score_at_application: int
    status: LoanStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[UUID]

    model_config = {"from_attributes": True}


class LoanReviewRequest(BaseModel):
    status: LoanStatus
