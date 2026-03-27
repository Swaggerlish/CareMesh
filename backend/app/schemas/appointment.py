from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.hospital import HospitalOut


class AppointmentCreate(BaseModel):
    hospital_id: int
    patient_name: str
    patient_email: EmailStr
    patient_phone: str
    reason: str
    scheduled_for: datetime
    amount_kobo: int = 500000

    @field_validator('scheduled_for')
    @classmethod
    def validate_scheduled_for(cls, value: datetime) -> datetime:
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value <= now:
            raise ValueError('Appointment date and time must be in the future.')
        return value


class AppointmentOut(BaseModel):
    id: int
    hospital_id: int
    patient_name: str
    patient_email: str
    patient_phone: str
    reason: str
    scheduled_for: datetime
    status: str
    payment_status: str

    class Config:
        from_attributes = True


class AppointmentDetailOut(AppointmentOut):
    hospital: HospitalOut

    class Config:
        from_attributes = True
