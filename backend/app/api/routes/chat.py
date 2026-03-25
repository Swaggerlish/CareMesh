from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import ai_service
from app.core.config import settings

router = APIRouter()


@router.post('/', response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    reply, used_context, model = await ai_service.chat(
        payload.message,
        db,
        state=payload.hospital_state,
        lga=payload.hospital_lga,
    )
    return ChatResponse(
        reply=reply,
        model=model,
        used_hospital_context=used_context,
    )
