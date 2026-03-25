from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hospital import Hospital

logger = logging.getLogger(__name__)


class HuggingFaceAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str, code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class AIService:
    def _candidate_models(self) -> list[str]:
        models = [settings.hf_model]
        extra_models = [
            item.strip()
            for item in settings.hf_fallback_models.split(',')
            if item.strip()
        ]
        for model in extra_models:
            if model not in models:
                models.append(model)
        return models

    def build_hospital_context(self, db: Session, state: str | None, lga: str | None) -> str:
        query = db.query(Hospital)
        if state:
            query = query.filter(Hospital.state.ilike(f'%{state}%'))
        if lga:
            query = query.filter(Hospital.lga.ilike(f'%{lga}%'))

        hospitals = query.order_by(Hospital.name.asc()).limit(5).all()
        if not hospitals:
            return 'No matching hospital data available in the local directory.'

        lines: list[str] = []
        for hospital in hospitals:
            facilities = []
            if hospital.services:
                facilities.extend(hospital.services.split(', '))
            if hospital.capabilities:
                facilities.extend(hospital.capabilities.split(', '))
            facilities_str = ', '.join(set(f.strip() for f in facilities if f.strip()))
            lines.append(
                f'- {hospital.name} | {hospital.lga}, {hospital.state} | '
                f'specialties: {hospital.specialties} | '
                f'available facilities: {facilities_str}'
            )
        return '\n'.join(lines)

    def _system_prompt(self, context: str) -> str:
        return (
            'You are CareMesh, a healthcare navigation assistant for Nigeria. '
            'Keep answers short, practical, and easy to understand. '
            'Do not claim to be a doctor and do not diagnose. '
            'For severe bleeding, chest pain, stroke signs, trouble breathing, seizures, '
            'suicidal thoughts, or pregnancy emergencies, tell the user to seek urgent medical care immediately. '
            'When relevant, use the hospital directory context below. '
            'If the directory does not confirm something, say you are not sure.\n\n'
            f'Hospital directory context:\n{context}'
        )

    async def _call_hugging_face(self, message: str, context: str, model: str) -> str:
        if not settings.hf_token:
            raise RuntimeError('HF_TOKEN is not configured.')

        headers = {
            'Authorization': f'Bearer {settings.hf_token}',
            'Content-Type': 'application/json',
        }
        combined_user_message = (
            f'{self._system_prompt(context)}\n\n'
            f'User request:\n{message}'
        )
        payload: dict[str, Any] = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': combined_user_message},
            ],
            'max_tokens': settings.hf_max_tokens,
            'temperature': settings.hf_temperature,
            'chat_template_kwargs': {
                'enable_thinking': False,
            },
        }

        async with httpx.AsyncClient(timeout=settings.hf_timeout_seconds) as client:
            response = await client.post(settings.hf_base_url, headers=headers, json=payload)
            if response.is_error:
                try:
                    error_payload = response.json()
                except ValueError:
                    error_payload = None
                error = error_payload.get('error') if isinstance(error_payload, dict) else None
                error_message = error.get('message') if isinstance(error, dict) else response.text
                error_code = error.get('code') if isinstance(error, dict) else None
                raise HuggingFaceAPIError(
                    response.status_code,
                    f'Hugging Face API error {response.status_code}: {error_message}',
                    code=error_code,
                )
            data = response.json()

        try:
            return data['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f'Unexpected Hugging Face response: {data}') from exc

    async def chat(self, message: str, db: Session, state: str | None = None, lga: str | None = None) -> tuple[str, bool, str]:
        context = self.build_hospital_context(db, state, lga)
        used_context = 'No matching hospital data' not in context

        candidate_models = self._candidate_models()
        primary_model = candidate_models[0]
        errors: list[str] = []

        for index, model in enumerate(candidate_models):
            try:
                reply = await self._call_hugging_face(message=message, context=context, model=model)
                if not reply:
                    reply = 'I could not generate a response right now. Please try again.'
                if index == 0:
                    return reply, used_context, model
                support_note = (
                    f'CareMesh AI switched to fallback model `{model}` because '
                    f'the selected model `{primary_model}` was unavailable on your enabled provider.\n\n'
                )
                return f'{support_note}{reply}', used_context, model
            except HuggingFaceAPIError as exc:
                logger.exception('Hugging Face model failed: %s', model)
                errors.append(f'{model}: {exc}')
                continue
            except Exception as exc:
                logger.exception('Unexpected Hugging Face failure: %s', model)
                errors.append(f'{model}: {exc}')
                continue

        fallback = (
            f'CareMesh AI could not use the selected model `{primary_model}` or any configured fallback model. '
            'The configured Hugging Face router models are currently unavailable for your provider setup.'
        )
        if settings.app_debug and errors:
            fallback = f'{fallback} Debug reason: {" | ".join(errors)}'
        return fallback, False, 'fallback-assistant'


ai_service = AIService()
