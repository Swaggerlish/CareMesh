from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.hospital import Hospital
from app.schemas.hospital import HospitalOut
from app.schemas.planning import PlanningResponse
from app.services.planning_service import build_planning_snapshot

router = APIRouter()


def _registry_hospital_query(db: Session, country: str | None):
    query = db.query(Hospital).filter(Hospital.registry_id.isnot(None))
    if country:
        query = query.filter(Hospital.country == country)
    return query


@router.get('/planning/deserts', response_model=PlanningResponse)
def get_planning_snapshot(
    country: str | None = Query(default='Nigeria'),
    state: str | None = Query(default=None),
    lga: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if country and country.lower() != 'nigeria':
        raise HTTPException(status_code=400, detail='Planning analytics currently support Nigeria only')
    return build_planning_snapshot(db, state=state, lga=lga)


@router.get('/states', response_model=list[str])
def list_states(
    country: str | None = Query(default='Nigeria'),
    db: Session = Depends(get_db),
):
    rows = (
        _registry_hospital_query(db, country)
        .with_entities(Hospital.state)
        .distinct()
        .order_by(Hospital.state.asc())
        .all()
    )
    return [state for state, in rows if state]


@router.get('/lgas', response_model=list[str])
def list_lgas(
    country: str | None = Query(default='Nigeria'),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = _registry_hospital_query(db, country)
    if state:
        query = query.filter(Hospital.state == state)
    rows = query.with_entities(Hospital.lga).distinct().order_by(Hospital.lga.asc()).all()
    return [lga for lga, in rows if lga]


@router.get('/', response_model=list[HospitalOut])
def list_hospitals(
    country: str | None = Query(default='Nigeria'),
    state: str | None = Query(default=None),
    lga: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = _registry_hospital_query(db, country)
    if state:
        query = query.filter(Hospital.state == state)
    if lga:
        query = query.filter(Hospital.lga == lga)
    if q:
        search = f'%{q}%'
        query = query.filter(
            Hospital.name.ilike(search)
            | Hospital.specialties.ilike(search)
            | Hospital.services.ilike(search)
            | Hospital.capabilities.ilike(search)
        )
    return query.order_by(Hospital.state.asc(), Hospital.lga.asc(), Hospital.name.asc()).all()


@router.get('/validate/{registry_id}', response_model=HospitalOut)
def validate_hospital(registry_id: str, db: Session = Depends(get_db)):
    hospital = db.query(Hospital).filter(Hospital.registry_id == registry_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found in registry")
    return hospital
