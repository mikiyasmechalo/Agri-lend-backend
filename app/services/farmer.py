from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.farmer import FarmerProfile, FarmParcel
from app.models.auth import User
from app.schemas.farmer import FarmerRegistrationHub, FarmParcelCreate
from app.core.security import hash_password
from datetime import datetime, timezone
from app.services.geospatial import GeospatialService


class FarmerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_hub(self, data: FarmerRegistrationHub) -> tuple[FarmerProfile, FarmParcel | None]:
        from app.models.auth import Role
        result = await self.db.execute(select(Role).where(Role.name == "Farmer"))
        role = result.scalar_one_or_none()
        if not role:
            raise ValueError("Farmer role not found")
        user = User(
            email=data.email,
            phone_number=data.phone_number,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role_id=role.id,
        )
        self.db.add(user)
        await self.db.flush()

        profile = FarmerProfile(
            user_id=user.id,
            full_name=data.full_name,
            national_id=data.national_id,
            phone_number=data.phone_number,
            gps_coordinates=data.gps_coordinates,
            land_proof_document=data.land_proof_document,
            locale=data.locale,
        )
        self.db.add(profile)
        await self.db.flush()

        parcel = None
        if data.crop_type and data.farm_size_hectares and data.region:
            parcel = FarmParcel(
                farmer_id=profile.id,
                parcel_name=f"{data.full_name}'s Farm",
                size_hectares=data.farm_size_hectares,
                primary_crop=data.crop_type,
                region=data.region,
            )
            self.db.add(parcel)
            await self.db.flush()

        return profile, parcel

    async def set_consent(self, farmer_id: str, consent: bool) -> FarmerProfile | None:
        profile = await self.get_profile(farmer_id)
        if not profile:
            return None
        profile.consent_status = consent
        profile.consent_date = datetime.now(timezone.utc) if consent else None
        await self.db.flush()
        return profile

    async def get_profile(self, farmer_id: str) -> FarmerProfile | None:
        result = await self.db.execute(select(FarmerProfile).where(FarmerProfile.id == farmer_id))
        return result.scalar_one_or_none()

    async def get_profile_by_user(self, user_id: str) -> FarmerProfile | None:
        result = await self.db.execute(select(FarmerProfile).where(FarmerProfile.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_profile_by_email(self, email: str) -> FarmerProfile | None:
        result = await self.db.execute(
            select(FarmerProfile).join(User, FarmerProfile.user_id == User.id).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def add_parcel(self, data: FarmParcelCreate) -> FarmParcel:
        parcel = FarmParcel(**data.model_dump())
        self.db.add(parcel)
        await self.db.flush()
        return parcel

    async def get_parcels(self, farmer_id: str) -> list[FarmParcel]:
        result = await self.db.execute(select(FarmParcel).where(FarmParcel.farmer_id == farmer_id))
        return list(result.scalars().all())

    async def get_farm_status(self, farmer_id: str) -> dict:
        parcels = await self.get_parcels(farmer_id)
        ndvi_trend = []
        ndvi_current = None
        if parcels:
            geo = GeospatialService()
            try:
                ndvi_trend = await geo.get_ndvi_timeseries(str(parcels[0].id), days=90)
                ndvi_current = ndvi_trend[-1]["ndvi_value"] if ndvi_trend else None
            except Exception:
                ndvi_trend = []
        health_label = "Good"
        if ndvi_current is not None:
            if ndvi_current < 0.3:
                health_label = "Poor"
            elif ndvi_current < 0.5:
                health_label = "Fair"
        return {
            "farmer_id": farmer_id,
            "ndvi_current": ndvi_current,
            "ndvi_trend": ndvi_trend,
            "crop_health_label": health_label,
        }
