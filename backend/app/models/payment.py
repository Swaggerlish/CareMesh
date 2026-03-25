from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Payment(TimestampMixin, Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey('appointments.id'))
    txn_ref: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    amount_kobo: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default='NGN')
    status: Mapped[str] = mapped_column(String(30), default='PENDING')
    provider: Mapped[str] = mapped_column(String(50), default='INTERSWITCH')
    provider_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    appointment = relationship('Appointment', back_populates='payments')
