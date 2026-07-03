from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.bank import BankPartnerCreate, BankPartnerResponse
from app.core.dependencies import get_current_user, require_roles
from app.models.bank import BankPartner

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
    from sqlalchemy import select
    result = await db.execute(select(BankPartner))
    return list(result.scalars().all())
