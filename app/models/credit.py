import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, Numeric, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import enum


class RiskTier(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CreditScoreRecord(TimestampMixin, Base):
    __tablename__ = "credit_score_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    score_value: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_tier: Mapped[RiskTier] = mapped_column(SAEnum(RiskTier), nullable=False)
    geospatial_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    transactional_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    alternative_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    farmer: Mapped["FarmerProfile"] = relationship("FarmerProfile", back_populates="credit_scores")
