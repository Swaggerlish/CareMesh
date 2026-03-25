from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.hospital import Hospital
from app.schemas.appointment import AppointmentCreate, AppointmentDetailOut, AppointmentOut
from app.schemas.payment import PaymentInitResponse
from app.services.payment_service import create_payment_for_appointment
from app.core.config import settings

router = APIRouter()


@router.post('/', response_model=PaymentInitResponse)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    hospital = db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail='Hospital not found')

    appointment = Appointment(
        hospital_id=payload.hospital_id,
        patient_name=payload.patient_name,
        patient_email=payload.patient_email,
        patient_phone=payload.patient_phone,
        reason=payload.reason,
        scheduled_for=payload.scheduled_for,
        status='PENDING',
        payment_status='UNPAID',
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    payment = create_payment_for_appointment(db, appointment, payload.amount_kobo)

    return PaymentInitResponse(
        appointment_id=appointment.id,
        merchant_code=settings.interswitch_merchant_code,
        pay_item_id=settings.interswitch_pay_item_id,
        txn_ref=payment.txn_ref,
        amount=payment.amount_kobo,
        redirect_url=settings.app_redirect_url,
        mode=settings.interswitch_mode.upper(),
    )


@router.get('/', response_model=list[AppointmentOut])
def list_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).order_by(Appointment.created_at.desc()).all()


@router.get('/{appointment_id}', response_model=AppointmentDetailOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail='Appointment not found')
    return appointment
