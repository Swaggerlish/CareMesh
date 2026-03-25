from __future__ import annotations

import logging
from secrets import compare_digest

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import func

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.hospital import Hospital
from app.models.hospital_capacity import HospitalCapacity
from app.models.lga_profile import LgaProfile
from app.services.bootstrap_data import ensure_bootstrap_data

router = APIRouter()
logger = logging.getLogger(__name__)

bootstrap_status: dict[str, object] = {
    'state': 'idle',
    'message': 'No bootstrap has been started yet.',
    'before': None,
    'after': None,
}


def _snapshot_counts() -> dict[str, int]:
    db = SessionLocal()
    try:
        return {
            'hospital_count': db.query(func.count(Hospital.id)).scalar() or 0,
            'registry_hospital_count': db.query(func.count(Hospital.id)).filter(Hospital.registry_id.isnot(None)).scalar() or 0,
            'mapped_hospital_count': (
                db.query(func.count(Hospital.id))
                .filter(Hospital.latitude.isnot(None), Hospital.longitude.isnot(None))
                .scalar()
                or 0
            ),
            'lga_profile_count': db.query(func.count(LgaProfile.id)).scalar() or 0,
            'hospital_capacity_count': db.query(func.count(HospitalCapacity.id)).scalar() or 0,
        }
    finally:
        db.close()


def _run_bootstrap_job() -> None:
    global bootstrap_status
    before = _snapshot_counts()
    bootstrap_status = {
        'state': 'running',
        'message': 'Bootstrap is running.',
        'before': before,
        'after': None,
    }
    logger.info('Bootstrap job started: before=%s', before)
    try:
        ensure_bootstrap_data()
        after = _snapshot_counts()
        bootstrap_status = {
            'state': 'completed',
            'message': 'Bootstrap completed successfully.',
            'before': before,
            'after': after,
        }
        logger.info('Bootstrap job completed: after=%s', after)
    except Exception as exc:
        bootstrap_status = {
            'state': 'failed',
            'message': str(exc),
            'before': before,
            'after': None,
        }
        logger.exception('Bootstrap job failed')


@router.get('/bootstrap')
def bootstrap_debug_data(background_tasks: BackgroundTasks, token: str = Query(default='')) -> dict[str, object]:
    expected_token = settings.bootstrap_debug_token.strip()
    if not expected_token:
        raise HTTPException(status_code=404, detail='Bootstrap endpoint is disabled')
    if not token or not compare_digest(token, expected_token):
        raise HTTPException(status_code=403, detail='Invalid bootstrap token')

    if bootstrap_status.get('state') == 'running':
        return {
            'message': 'Bootstrap is already running.',
            'status': bootstrap_status,
        }

    background_tasks.add_task(_run_bootstrap_job)
    return {
        'message': 'Bootstrap started',
        'status': bootstrap_status,
    }


@router.get('/bootstrap/status')
def bootstrap_debug_status(token: str = Query(default='')) -> dict[str, object]:
    expected_token = settings.bootstrap_debug_token.strip()
    if not expected_token:
        raise HTTPException(status_code=404, detail='Bootstrap endpoint is disabled')
    if not token or not compare_digest(token, expected_token):
        raise HTTPException(status_code=403, detail='Invalid bootstrap token')
    return bootstrap_status
