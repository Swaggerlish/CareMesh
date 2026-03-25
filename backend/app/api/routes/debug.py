from __future__ import annotations

from secrets import compare_digest

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.hospital import Hospital
from app.models.hospital_capacity import HospitalCapacity
from app.models.lga_profile import LgaProfile
from app.services.bootstrap_data import ensure_bootstrap_data

router = APIRouter()


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


@router.get('/bootstrap')
def bootstrap_debug_data(token: str = Query(default='')) -> dict[str, object]:
    expected_token = settings.bootstrap_debug_token.strip()
    if not expected_token:
        raise HTTPException(status_code=404, detail='Bootstrap endpoint is disabled')
    if not token or not compare_digest(token, expected_token):
        raise HTTPException(status_code=403, detail='Invalid bootstrap token')

    before = _snapshot_counts()
    ensure_bootstrap_data()
    after = _snapshot_counts()

    return {
        'message': 'Bootstrap completed',
        'before': before,
        'after': after,
    }
