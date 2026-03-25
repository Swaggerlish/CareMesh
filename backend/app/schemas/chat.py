from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    hospital_state: str | None = None
    hospital_lga: str | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    used_hospital_context: bool
