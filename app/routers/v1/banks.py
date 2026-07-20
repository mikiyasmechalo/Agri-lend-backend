from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sa_func
from typing import Optional
from app.db.session import get_db
from app.schemas.bank import BankPartnerCreate, BankPartnerResponse, BankSettingsUpdate
from app.schemas import PaginatedResponse
from app.core.dependencies import get_current_user, require_roles
from app.models.bank import BankPartner
from app.services.auth import AuthService

router = APIRouter(prefix="/banks", tags=["Banks"])


@router.post("/", response_model=BankPartnerResponse, status_code=201,
             summary="Create a bank partner",
             description="Register a new bank partner. Requires Platform Admin.")
async def create_bank(
    data: BankPartnerCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    bank = BankPartner(bank_name=data.bank_name, subscription_tier=data.subscription_tier)
    db.add(bank)
    await db.flush()
    return bank


@router.get("/",
            summary="List bank partners",
            description="Returns a paginated list of all registered bank partners.")
async def list_banks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    count_q = await db.execute(select(sa_func.count(BankPartner.id)))
    total = count_q.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        select(BankPartner).order_by(BankPartner.onboarding_date.desc()).offset(offset).limit(page_size)
    )
    banks = list(result.scalars().all())
    return {
        "items": banks,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size) if total > 0 else 0,
    }


@router.get("/{bank_id}", response_model=BankPartnerResponse,
            summary="Get bank details",
            description="Returns details for a specific bank partner.",
            responses={404: {"description": "Bank not found"}})
async def get_bank(
    bank_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Bank Administrator", "Platform Admin")),
):
    result = await db.execute(select(BankPartner).where(BankPartner.id == bank_id))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    return bank


@router.patch("/{bank_id}/settings",
              summary="Update bank settings",
              description="Update bank name or subscription tier. Requires Bank Administrator or Platform Admin.",
              responses={404: {"description": "Bank not found"}})
async def update_bank_settings(
    bank_id: str,
    data: BankSettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("Bank Administrator", "Platform Admin")),
):
    result = await db.execute(select(BankPartner).where(BankPartner.id == bank_id))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    if data.bank_name is not None:
        bank.bank_name = data.bank_name
    if data.subscription_tier is not None:
        bank.subscription_tier = data.subscription_tier
    await db.flush()
    audit = AuthService(db)
    await audit.log_audit(
        user_id=current_user["sub"],
        action="UPDATE_BANK_SETTINGS",
        resource="BankPartner",
        resource_id=bank_id,
        ip=request.client.host if request.client else None,
    )
    return {"detail": "Bank settings updated"}
