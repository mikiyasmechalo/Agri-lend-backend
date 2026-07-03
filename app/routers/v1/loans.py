from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.schemas.loan import LoanApplicationCreate, LoanApplicationResponse, LoanReviewRequest
from app.models.loan import LoanStatus
from app.services.loan import LoanService
from app.services.credit import CreditService
from app.core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/", response_model=LoanApplicationResponse, status_code=201)
async def create_loan(
    data: LoanApplicationCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Farmer", "Platform Admin")),
):
    credit_service = CreditService(db)
    latest = await credit_service.get_latest_score(str(data.farmer_id))
    score = latest.score_value if latest else 300

    loan_service = LoanService(db)
    return await loan_service.create_application(data, score)


@router.get("/", response_model=list[LoanApplicationResponse])
async def list_loans(
    farmer_id: Optional[str] = None,
    status: Optional[LoanStatus] = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    service = LoanService(db)
    return await service.get_applications(farmer_id, status)


@router.patch("/{app_id}/review", response_model=LoanApplicationResponse)
async def review_loan(
    app_id: str,
    data: LoanReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("Loan Officer", "Bank Analyst", "Platform Admin")),
):
    service = LoanService(db)
    app = await service.review_application(app_id, data.status, current_user["sub"])
    if not app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    return app
