from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.loan import LoanApplication, LoanStatus
from app.schemas.loan import LoanApplicationCreate
from datetime import datetime, timezone


class LoanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(self, data: LoanApplicationCreate, score: int) -> LoanApplication:
        app = LoanApplication(
            farmer_id=data.farmer_id,
            bank_id=data.bank_id,
            requested_amount=data.requested_amount,
            loan_purpose=data.loan_purpose,
            credit_score_at_application=score,
        )
        self.db.add(app)
        await self.db.flush()
        return app

    async def get_applications(self, farmer_id: str | None = None, status: LoanStatus | None = None) -> list[LoanApplication]:
        query = select(LoanApplication).order_by(desc(LoanApplication.submitted_at))
        if farmer_id:
            query = query.where(LoanApplication.farmer_id == farmer_id)
        if status:
            query = query.where(LoanApplication.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def review_application(self, app_id: str, status: LoanStatus, reviewer_id: str) -> LoanApplication | None:
        result = await self.db.execute(select(LoanApplication).where(LoanApplication.id == app_id))
        app = result.scalar_one_or_none()
        if not app:
            return None
        app.status = status
        app.reviewed_by = reviewer_id
        app.reviewed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return app
