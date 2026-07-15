from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.credit import CreditScoreRecord
from app.schemas.credit import ExplainabilityResponse
from app.services.scoring import ScoringService


class CreditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_score(self, farmer_id: str) -> CreditScoreRecord | None:
        result = await self.db.execute(
            select(CreditScoreRecord)
            .where(CreditScoreRecord.farmer_id == farmer_id)
            .order_by(desc(CreditScoreRecord.calculated_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_score_history(self, farmer_id: str) -> list[CreditScoreRecord]:
        result = await self.db.execute(
            select(CreditScoreRecord)
            .where(CreditScoreRecord.farmer_id == farmer_id)
            .order_by(desc(CreditScoreRecord.calculated_at))
        )
        return list(result.scalars().all())

    async def get_explainability(self, farmer_id: str, score: CreditScoreRecord) -> ExplainabilityResponse:
        try:
            scoring = ScoringService()
            ai_explain = await scoring.get_explainability(farmer_id)
            factors = ai_explain.get("features", [])
            summary = ai_explain.get("summary", "")
        except Exception:
            factors = [
                {"name": "Satellite crop health", "importance": 0.35, "value": f"{score.geospatial_score:.2f}"},
                {"name": "Sales & payment history", "importance": 0.35, "value": f"{score.transactional_score:.2f}"},
                {"name": "Mobile money activity", "importance": 0.20, "value": f"{score.alternative_score:.2f}"},
                {"name": "Climate resilience", "importance": 0.10, "value": f"{score.alternative_score:.2f}"},
            ]
            summary = (
                f"Your credit score is {score.score_value} ({score.risk_tier.value}). "
                f"The main factors are your satellite crop health data and sales history."
            )

        return ExplainabilityResponse(
            farmer_id=farmer_id,
            score_value=score.score_value,
            risk_tier=score.risk_tier.value,
            summary=summary,
            top_factors=factors,
        )
