from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Hospital(TimestampMixin, Base):
    __tablename__ = 'hospitals'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(120), default='Nigeria', index=True)
    state: Mapped[str] = mapped_column(String(120), index=True)
    lga: Mapped[str] = mapped_column(String(120), index=True)
    address: Mapped[str] = mapped_column(String(255))
    specialties: Mapped[str] = mapped_column(Text)
    services: Mapped[str] = mapped_column(Text)
    capabilities: Mapped[str] = mapped_column(Text)
    registry_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    appointments = relationship('Appointment', back_populates='hospital', cascade='all, delete-orphan')
    capacity_profile = relationship('HospitalCapacity', back_populates='hospital', uselist=False, cascade='all, delete-orphan')
