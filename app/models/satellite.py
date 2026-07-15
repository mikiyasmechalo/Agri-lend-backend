import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SatelliteObservation(Base):
    __tablename__ = "satellite_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farm_parcels.id"), nullable=False, index=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    ndvi_value: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    cloud_cover_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    data_source: Mapped[str] = mapped_column(String(50), default="Sentinel-2")
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )

    parcel: Mapped["FarmParcel"] = relationship("FarmParcel", back_populates="observations")
