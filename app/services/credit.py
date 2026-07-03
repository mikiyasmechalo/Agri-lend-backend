from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.credit import CreditScoreRecord


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
