from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.schemas.hospital import HospitalOut


class AppointmentCreate(BaseModel):
    hospital_id: int
    patient_name: str
    patient_email: EmailStr
    patient_phone: str
    reason: str
    scheduled_for: datetime
    amount_kobo: int = 500000


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
