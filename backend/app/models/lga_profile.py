from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class LgaProfile(TimestampMixin, Base):
    __tablename__ = 'lga_profiles'
    __table_args__ = (UniqueConstraint('state', 'lga', name='uq_lga_profile_state_lga'),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    state: Mapped[str] = mapped_column(String(120), index=True)
    lga: Mapped[str] = mapped_column(String(120), index=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    centroid_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_hospital_registry_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nearest_hospital_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nearest_care_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_travel_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_road_speed_kph: Mapped[float | None] = mapped_column(Float, nullable=True)
    road_access_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    rurality_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
