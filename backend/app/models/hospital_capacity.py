from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class HospitalCapacity(TimestampMixin, Base):
    __tablename__ = 'hospital_capacities'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), unique=True, index=True)
    bed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doctor_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nurse_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ambulance_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_emergency_unit: Mapped[bool] = mapped_column(Boolean, default=False)
    has_operating_theatre: Mapped[bool] = mapped_column(Boolean, default=False)
    has_icu: Mapped[bool] = mapped_column(Boolean, default=False)
    has_blood_bank: Mapped[bool] = mapped_column(Boolean, default=False)

    hospital = relationship('Hospital', back_populates='capacity_profile')
