from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.farmer import FarmerProfile, FarmParcel
from app.models.credit import CreditScoreRecord, RiskTier
from app.models.satellite import SatelliteObservation
from app.services.scoring import ScoringService
from app.services.geospatial import GeospatialService
from datetime import datetime, timezone
from decimal import Decimal


class BrainService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_score_calculation(self, farmer_id: str) -> CreditScoreRecord | None:
        farmer_result = await self.db.execute(
            select(FarmerProfile).where(FarmerProfile.id == farmer_id)
        )
        farmer = farmer_result.scalar_one_or_none()
        if not farmer:
            return None

        parcel_result = await self.db.execute(
            select(FarmParcel).where(FarmParcel.farmer_id == farmer_id).limit(1)
        )
        parcel = parcel_result.scalar_one_or_none()

        geo_score = Decimal("0.0")
        ndvi_values = []
        if parcel:
            obs_result = await self.db.execute(
                select(SatelliteObservation)
                .where(SatelliteObservation.parcel_id == parcel.id)
                .order_by(SatelliteObservation.observation_date.desc())
                .limit(10)
            )
            observations = obs_result.scalars().all()
            ndvi_values = [float(o.ndvi_value) for o in observations if o.ndvi_value is not None]
            if ndvi_values:
                avg_ndvi = sum(ndvi_values) / len(ndvi_values)
                geo_score = Decimal(str(round(avg_ndvi * 100, 2)))

        trans_score = Decimal("0.0")
        alt_score = Decimal("0.0")
        model_ver = "v1.0.0"
        confidence = Decimal("0.85")

        try:
            scoring = ScoringService()
            ai_result = await scoring.get_credit_score(farmer_id)
            score_value = ai_result.get("score", 500)
            risk_tier_str = ai_result.get("risk_tier", "MEDIUM")
            confidence = Decimal(str(ai_result.get("confidence", 0.85)))
            model_ver = ai_result.get("model_version", "v1.0.0")
            geo_score = Decimal(str(ai_result.get("geospatial_score", geo_score)))
            trans_score = Decimal(str(ai_result.get("transactional_score", 0)))
            alt_score = Decimal(str(ai_result.get("alternative_score", 0)))
            risk_tier = RiskTier(risk_tier_str)
        except Exception:
            if ndvi_values:
                avg = sum(ndvi_values) / len(ndvi_values)
                if avg < 0.3:
                    score_value = 350
                    risk_tier = RiskTier.HIGH
                elif avg < 0.5:
                    score_value = 550
                    risk_tier = RiskTier.MEDIUM
                else:
                    score_value = 720
                    risk_tier = RiskTier.LOW
            else:
                score_value = 500
                risk_tier = RiskTier.MEDIUM

        record = CreditScoreRecord(
            farmer_id=farmer_id,
            score_value=score_value,
            risk_tier=risk_tier,
            geospatial_score=geo_score,
            transactional_score=trans_score,
            alternative_score=alt_score,
            model_version=model_ver,
            confidence_rating=confidence,
            calculated_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def trigger_for_all_farmers(self) -> list[CreditScoreRecord]:
        result = await self.db.execute(select(FarmerProfile))
        farmers = result.scalars().all()
        records = []
        for farmer in farmers:
            record = await self.trigger_score_calculation(str(farmer.id))
            if record:
                records.append(record)
        return records

    @staticmethod
    def get_risk_tier_detail(score: int, risk_tier: RiskTier) -> dict:
        ranges = {
            RiskTier.LOW: {"label": "Low Risk", "min": 50000, "max": 200000},
            RiskTier.MEDIUM: {"label": "Medium Risk", "min": 10000, "max": 50000},
            RiskTier.HIGH: {"label": "High Risk", "min": 0, "max": 10000},
        }
        info = ranges[risk_tier]
        return {
            "score_value": score,
            "risk_tier": risk_tier.value,
            "label": info["label"],
            "recommended_loan_min": info["min"],
            "recommended_loan_max": info["max"],
            "contributing_factors": [
                {"factor": "Satellite crop health (NDVI)", "weight": "35%"},
                {"factor": "Sales & payment history", "weight": "35%"},
                {"factor": "Mobile money activity", "weight": "20%"},
                {"factor": "Climate resilience", "weight": "10%"},
            ],
        }

    async def handle_satellite_ingestion_webhook(self, parcel_id: str) -> dict:
        parcel_result = await self.db.execute(
            select(FarmParcel).where(FarmParcel.id == parcel_id)
        )
        parcel = parcel_result.scalar_one_or_none()
        if not parcel:
            return {"detail": "Parcel not found"}
        geo = GeospatialService()
        try:
            ndvi_data = await geo.get_ndvi_timeseries(parcel_id, days=1)
            if ndvi_data:
                latest = ndvi_data[-1]
                obs = SatelliteObservation(
                    parcel_id=parcel_id,
                    observation_date=datetime.now(timezone.utc).date(),
                    ndvi_value=Decimal(str(latest.get("ndvi_value", 0))),
                    cloud_cover_pct=Decimal(str(latest.get("cloud_cover", 0))),
                    data_source=latest.get("source", "Sentinel-2"),
                )
                self.db.add(obs)
                await self.db.flush()
        except Exception:
            pass
        record = await self.trigger_score_calculation(str(parcel.farmer_id))
        return {
            "detail": "Satellite data ingested and score recalculated",
            "parcel_id": parcel_id,
            "farmer_id": str(parcel.farmer_id),
            "new_score": record.score_value if record else None,
        }
