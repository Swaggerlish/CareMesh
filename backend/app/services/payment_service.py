from __future__ import annotations

import base64
import json
import uuid

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.payment import Payment

SUCCESS_CODES = {'0', '00', '200', '90000'}
SUCCESS_STATUSES = {'APPROVED', 'COMPLETED', 'PAID', 'SUCCESS', 'SUCCESSFUL'}
PENDING_CODES = {'09'}
PENDING_STATUSES = {'INITIATED', 'PENDING', 'PROCESSING'}


def create_payment_for_appointment(db: Session, appointment: Appointment, amount_kobo: int) -> Payment:
    txn_ref = f'caremesh-{uuid.uuid4().hex[:16]}'
    payment = Payment(
        appointment_id=appointment.id,
        txn_ref=txn_ref,
        amount_kobo=amount_kobo,
        currency='NGN',
        status='PENDING',
        provider='INTERSWITCH',
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.strip().upper()
    return normalized in {'', 'MX-TEST', '101'} or normalized.startswith('YOUR_') or normalized.startswith('DEMO_')


def _collections_base_url() -> str:
    if settings.interswitch_collections_base_url:
        return settings.interswitch_collections_base_url.rstrip('/')
    if settings.interswitch_mode.upper() == 'TEST':
        return 'https://qa.interswitchng.com'
    return 'https://webpay.interswitchng.com'


def _passport_base_url() -> str:
    if settings.interswitch_passport_base_url:
        return settings.interswitch_passport_base_url.rstrip('/')
    if settings.interswitch_mode.upper() == 'TEST':
        return 'https://qa.interswitchng.com'
    return 'https://passport-v2.k8.isw.la'


def _resolve_response_value(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ''):
            return str(value).strip()
    return ''


def _extract_amount(payload: dict) -> str:
    return _resolve_response_value(payload, 'amount', 'Amount')


def _is_success_payload(payload: dict, payment: Payment) -> bool:
    amount_matches = _extract_amount(payload) == str(payment.amount_kobo)
    code = _resolve_response_value(payload, 'responseCode', 'ResponseCode', 'code').upper()
    status = _resolve_response_value(
        payload,
        'status',
        'Status',
        'paymentStatus',
        'PaymentStatus',
        'transactionStatus',
        'TransactionStatus',
    ).upper()
    approved = _resolve_response_value(payload, 'approved', 'Approved').upper()

    success_flag = code in SUCCESS_CODES or status in SUCCESS_STATUSES or approved == 'TRUE'
    return amount_matches and success_flag


def _is_pending_payload(payload: dict) -> bool:
    code = _resolve_response_value(payload, 'responseCode', 'ResponseCode', 'code').upper()
    status = _resolve_response_value(
        payload,
        'status',
        'Status',
        'paymentStatus',
        'PaymentStatus',
        'transactionStatus',
        'TransactionStatus',
    ).upper()
    return code in PENDING_CODES or status in PENDING_STATUSES


def _build_token_auth_header() -> str:
    raw = f'{settings.interswitch_client_id}:{settings.interswitch_secret_key}'
    encoded = base64.b64encode(raw.encode('utf-8')).decode('ascii')
    return f'Basic {encoded}'


async def _get_access_token(client: httpx.AsyncClient) -> str | None:
    if _is_placeholder(settings.interswitch_client_id) or _is_placeholder(settings.interswitch_secret_key):
        return None

    token_url = f'{_passport_base_url()}/passport/oauth/token'
    response = await client.post(
        token_url,
        headers={
            'Authorization': _build_token_auth_header(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data={'grant_type': 'client_credentials'},
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get('access_token')


def _apply_success_state(payment: Payment, provider_response: dict) -> None:
    payment.status = 'SUCCESS'
    payment.provider_response_json = json.dumps(provider_response)
    payment.appointment.payment_status = 'PAID'
    payment.appointment.status = 'CONFIRMED'


def _apply_pending_state(payment: Payment, provider_response: dict) -> None:
    payment.status = 'PENDING'
    payment.provider_response_json = json.dumps(provider_response)
    payment.appointment.payment_status = 'UNPAID'
    payment.appointment.status = 'PENDING'


def _apply_failed_state(payment: Payment, provider_response: dict) -> None:
    payment.status = 'FAILED'
    payment.provider_response_json = json.dumps(provider_response)
    payment.appointment.payment_status = 'FAILED'
    payment.appointment.status = 'PENDING'


def _load_cached_provider_response(payment: Payment) -> dict | None:
    if not payment.provider_response_json:
        return None
    try:
        payload = json.loads(payment.provider_response_json)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


async def verify_payment_with_provider(db: Session, payment: Payment) -> dict:
    cached_response = _load_cached_provider_response(payment)
    if settings.interswitch_mode.upper() == 'TEST' and cached_response and cached_response.get('simulated'):
        return cached_response

    if _is_placeholder(settings.interswitch_merchant_code):
        payload = {
            'error': 'interswitch-config-missing',
            'detail': 'Set INTERSWITCH_MERCHANT_CODE before verifying live transactions.',
        }
        _apply_pending_state(payment, payload)
        db.commit()
        return payload

    base = _collections_base_url()
    url = (
        f"{base}/collections/api/v1/gettransaction.json?merchantcode={settings.interswitch_merchant_code}"
        f"&transactionreference={payment.txn_ref}&amount={payment.amount_kobo}"
    )

    async with httpx.AsyncClient(timeout=settings.interswitch_timeout_seconds) as client:
        try:
            headers = {'Content-Type': 'application/json'}
            access_token = await _get_access_token(client)
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'

            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            payload = {'error': 'interswitch-request-failed', 'detail': str(exc), 'url': url}
            _apply_pending_state(payment, payload)
            db.commit()
            return payload

    if _is_success_payload(payload, payment):
        _apply_success_state(payment, payload)
    elif _is_pending_payload(payload):
        _apply_pending_state(payment, payload)
    else:
        _apply_failed_state(payment, payload)

    db.commit()
    return payload
