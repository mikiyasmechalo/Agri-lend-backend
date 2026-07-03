from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.farmer import FarmerProfile, FarmParcel
from app.schemas.farmer import FarmerProfileCreate, FarmParcelCreate


class FarmerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_profile(self, data: FarmerProfileCreate) -> FarmerProfile:
        profile = FarmerProfile(**data.model_dump())
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def get_profile(self, farmer_id: str) -> FarmerProfile | None:
        result = await self.db.execute(select(FarmerProfile).where(FarmerProfile.id == farmer_id))
        return result.scalar_one_or_none()

    async def get_profile_by_user(self, user_id: str) -> FarmerProfile | None:
        result = await self.db.execute(select(FarmerProfile).where(FarmerProfile.user_id == user_id))
        return result.scalar_one_or_none()

    async def add_parcel(self, data: FarmParcelCreate) -> FarmParcel:
        parcel = FarmParcel(**data.model_dump())
        self.db.add(parcel)
        await self.db.flush()
        return parcel

    async def get_parcels(self, farmer_id: str) -> list[FarmParcel]:
        result = await self.db.execute(select(FarmParcel).where(FarmParcel.farmer_id == farmer_id))
        return list(result.scalars().all())
