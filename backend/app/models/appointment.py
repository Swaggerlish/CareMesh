from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Appointment(TimestampMixin, Base):
    __tablename__ = 'appointments'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'))
    patient_name: Mapped[str] = mapped_column(String(150))
    patient_email: Mapped[str] = mapped_column(String(255))
    patient_phone: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default='PENDING')
    payment_status: Mapped[str] = mapped_column(String(30), default='UNPAID')

    hospital = relationship('Hospital', back_populates='appointments')
    payments = relationship('Payment', back_populates='appointment', cascade='all, delete-orphan')
