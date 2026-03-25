import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.payment import Payment
from app.schemas.payment import PaymentVerifyResponse
from app.services.payment_service import verify_payment_with_provider

router = APIRouter()


@router.get('/verify/{txn_ref}', response_model=PaymentVerifyResponse)
async def verify_payment(txn_ref: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.txn_ref == txn_ref).first()
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found')

    provider_response = await verify_payment_with_provider(db, payment)
    db.refresh(payment)
    db.refresh(payment.appointment)
    return PaymentVerifyResponse(
        appointment_id=payment.appointment_id,
        txn_ref=payment.txn_ref,
        status=payment.status,
        appointment_status=payment.appointment.status,
        provider_response=provider_response,
    )


@router.post('/simulate/{txn_ref}')
async def simulate_payment(txn_ref: str, result: str = 'success', db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.txn_ref == txn_ref).first()
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found')

    if result.lower() == 'success':
        payment.status = 'SUCCESS'
        payment.appointment.payment_status = 'PAID'
        payment.appointment.status = 'CONFIRMED'
        provider_response = {'simulated': True, 'result': 'success', 'message': 'Simulated successful payment.'}
    else:
        payment.status = 'FAILED'
        payment.appointment.payment_status = 'FAILED'
        payment.appointment.status = 'PENDING'
        provider_response = {'simulated': True, 'result': 'failed', 'message': 'Simulated failed payment.'}

    payment.provider_response_json = json.dumps(provider_response)
    db.commit()
    return {
        'txn_ref': payment.txn_ref,
        'status': payment.status,
        'appointment_status': payment.appointment.status,
        'provider_response': provider_response,
    }


@router.post('/webhook')
async def payment_webhook(request: Request):
    payload = await request.json()
    return {'received': True, 'payload': payload}
