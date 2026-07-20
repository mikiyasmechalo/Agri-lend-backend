from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.credit import CreditScoreResponse
from app.services.brain import BrainService
from app.services.credit import CreditService
from app.core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/brain", tags=["Brain Integration"])


@router.post("/trigger-score/{farmer_id}", response_model=CreditScoreResponse)
async def trigger_score(
    farmer_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin", "Risk Analyst")),
):
    service = BrainService(db)
    record = await service.trigger_score_calculation(farmer_id)
    if not record:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return record


@router.post("/trigger-all")
async def trigger_all_scores(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = BrainService(db)
    records = await service.trigger_for_all_farmers()
    return {"detail": f"Scores calculated for {len(records)} farmers"}


@router.get("/risk-tier/{farmer_id}")
async def risk_tier_detail(
    farmer_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    credit = CreditService(db)
    score = await credit.get_latest_score(farmer_id)
    if not score:
        raise HTTPException(status_code=404, detail="No credit score found")
    return BrainService.get_risk_tier_detail(score.score_value, score.risk_tier)


@router.post("/webhook/satellite-ingestion")
async def satellite_ingestion_webhook(
    parcel_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = BrainService(db)
    return await service.handle_satellite_ingestion_webhook(parcel_id)
