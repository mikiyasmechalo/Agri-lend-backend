from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.farmer import (
    FarmerRegistrationHub, FarmerProfileResponse, FarmParcelCreate, FarmParcelResponse,
    ConsentRequest, FarmStatusResponse,
)
from app.schemas.credit import CreditScoreResponse, CreditScoreHistoryResponse, ExplainabilityResponse
from app.services.farmer import FarmerService
from app.services.credit import CreditService
from app.core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.post("/register", status_code=201)
async def register_hub(
    data: FarmerRegistrationHub,
    db: AsyncSession = Depends(get_db),
):
    service = FarmerService(db)
    try:
        profile, parcel = await service.register_hub(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "farmer_id": profile.id,
        "full_name": profile.full_name,
        "parcel_id": str(parcel.id) if parcel else None,
        "detail": "Farmer registered successfully",
    }


@router.get("/profile/{farmer_id}", response_model=FarmerProfileResponse)
async def get_profile(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    service = FarmerService(db)
    profile = await service.get_profile(farmer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return profile


@router.get("/me", response_model=FarmerProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = FarmerService(db)
    profile = await service.get_profile_by_user(current_user["sub"])
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return profile


@router.post("/consent", response_model=FarmerProfileResponse)
async def set_consent(
    farmer_id: str,
    data: ConsentRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    service = FarmerService(db)
    profile = await service.set_consent(farmer_id, data.consent)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return profile


@router.post("/consent/revoke", response_model=FarmerProfileResponse)
async def revoke_consent(
    farmer_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    service = FarmerService(db)
    profile = await service.set_consent(farmer_id, False)
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


@router.get("/{farmer_id}/explain", response_model=ExplainabilityResponse)
async def explain_score(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    credit_service = CreditService(db)
    score = await credit_service.get_latest_score(farmer_id)
    if not score:
        raise HTTPException(status_code=404, detail="No credit score found")
    return await credit_service.get_explainability(farmer_id, score)


@router.get("/{farmer_id}/farm-status", response_model=FarmStatusResponse)
async def get_farm_status(farmer_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    service = FarmerService(db)
    return await service.get_farm_status(farmer_id)
