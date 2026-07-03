import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, Numeric, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import enum


class LoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"


class LoanApplication(TimestampMixin, Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    loan_purpose: Mapped[str] = mapped_column(String(500), nullable=False)
    credit_score_at_application: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LoanStatus] = mapped_column(SAEnum(LoanStatus), default=LoanStatus.PENDING)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    farmer: Mapped["FarmerProfile"] = relationship("FarmerProfile", back_populates="loan_applications")
