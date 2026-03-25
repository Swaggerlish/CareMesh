from pydantic import BaseModel


class PaymentInitResponse(BaseModel):
    appointment_id: int
    merchant_code: str
    pay_item_id: str
    txn_ref: str
    amount: int
    redirect_url: str
    mode: str


class PaymentVerifyResponse(BaseModel):
    appointment_id: int
    txn_ref: str
    status: str
    appointment_status: str
    provider_response: dict
