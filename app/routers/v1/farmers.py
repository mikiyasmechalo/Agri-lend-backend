from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.farmer import FarmerProfileCreate, FarmerProfileResponse, FarmParcelCreate, FarmParcelResponse
from app.schemas.credit import CreditScoreResponse, CreditScoreHistoryResponse
from app.services.farmer import FarmerService
from app.services.credit import CreditService
from app.core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.post("/profile", response_model=FarmerProfileResponse, status_code=201)
async def create_profile(
    data: FarmerProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Farmer", "Platform Admin")),
):
    service = FarmerService(db)
    return await service.create_profile(data)


@router.get("/profile/{farmer_id}", response_model=FarmerProfileResponse)
async def get_profile(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    service = FarmerService(db)
    profile = await service.get_profile(farmer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return profile


@router.post("/parcels", response_model=FarmParcelResponse, status_code=201)
async def create_parcel(
    data: FarmParcelCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Farmer", "Platform Admin")),
):
    service = FarmerService(db)
    return await service.add_parcel(data)


@router.get("/{farmer_id}/parcels", response_model=list[FarmParcelResponse])
async def get_parcels(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    service = FarmerService(db)
    return await service.get_parcels(farmer_id)


@router.get("/{farmer_id}/credit-score", response_model=CreditScoreResponse)
async def get_credit_score(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    service = CreditService(db)
    score = await service.get_latest_score(farmer_id)
    if not score:
        raise HTTPException(status_code=404, detail="No credit score found")
    return score


@router.get("/{farmer_id}/credit-history", response_model=CreditScoreHistoryResponse)
async def get_credit_history(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    service = CreditService(db)
    scores = await service.get_score_history(farmer_id)
    return CreditScoreHistoryResponse(scores=scores, trend="")
