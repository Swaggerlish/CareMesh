from fastapi import APIRouter

from app.api.routes import appointments, chat, hospitals, payments

api_router = APIRouter()
api_router.include_router(hospitals.router, prefix='/hospitals', tags=['Hospitals'])
api_router.include_router(appointments.router, prefix='/appointments', tags=['Appointments'])
api_router.include_router(payments.router, prefix='/payments', tags=['Payments'])
api_router.include_router(chat.router, prefix='/chat', tags=['AI Chat'])
