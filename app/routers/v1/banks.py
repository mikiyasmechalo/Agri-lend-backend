from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.bank import BankPartnerCreate, BankPartnerResponse, BankSettingsUpdate
from app.core.dependencies import get_current_user, require_roles
from app.models.bank import BankPartner
from app.services.auth import AuthService

router = APIRouter(prefix="/banks", tags=["Banks"])


@router.post("/", response_model=BankPartnerResponse, status_code=201)
async def create_bank(
    data: BankPartnerCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    bank = BankPartner(bank_name=data.bank_name, subscription_tier=data.subscription_tier)
    db.add(bank)
    await db.flush()
    return bank


@router.get("/", response_model=list[BankPartnerResponse])
async def list_banks(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(BankPartner))
    return list(result.scalars().all())


@router.get("/{bank_id}", response_model=BankPartnerResponse)
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


@router.patch("/{bank_id}/settings")
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
