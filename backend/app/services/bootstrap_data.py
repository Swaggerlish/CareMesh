from __future__ import annotations

import csv
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.hospital import Hospital
from app.models.hospital_capacity import HospitalCapacity
from app.models.lga_profile import LgaProfile
from import_planning_data import import_hospital_capacities, import_lga_profiles

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'planning'
LGA_PROFILES_CSV = DATA_DIR / 'lga_profiles_nigeria_worldpop_v2.csv'
HOSPITAL_CAPACITIES_CSV = DATA_DIR / 'hospital_capacities_nigeria_grid3_baseline.csv'


def _map_services(level: str, option: str, ownership: str) -> tuple[str, str]:
    text = f'{level} {option}'.lower()
    ownership_text = ownership.lower()
    services = ['Consultation']
    capabilities = []

    if 'primary health center' in text or 'primary health clinic' in text:
        services.extend(['Antenatal care', 'General practice', 'Immunization'])
        capabilities.extend(['Basic maternity', 'Outpatient unit'])
    if 'health post' in text:
        services.extend(['Basic triage', 'Community health outreach'])
        capabilities.append('Referral point')
    if 'general hospital' in text or 'secondary' in text:
        services.extend(['Emergency care', 'Inpatient care', 'Surgery'])
        capabilities.extend(['Beds', 'Laboratory', 'Operating theatre'])
    if 'specialized hospital' in text:
        services.extend(['Diagnostics', 'Specialist care'])
        capabilities.extend(['Advanced laboratory', 'Specialist clinics'])
    if 'teaching/tertiary' in text or 'tertiary' in text:
        services.extend(['Critical care', 'Specialist care', 'Surgery'])
        capabilities.extend(['Advanced diagnostics', 'Blood bank', 'ICU'])

    if 'public' in ownership_text:
        capabilities.append('Government facilities')
    if 'private' in ownership_text:
        capabilities.append('Private facilities')

    return ', '.join(sorted(set(services))), ', '.join(sorted(set(capabilities)))


def _deterministic_coordinate_offset(seed: str) -> float:
    total = sum(ord(char) for char in seed)
    return ((total % 21) - 10) * 0.002


def _bootstrap_registry_hospitals_from_capacity_csv(csv_path: Path, db: Session) -> int:
    existing_registry_ids = {
        registry_id
        for registry_id, in db.query(Hospital.registry_id).filter(Hospital.registry_id.isnot(None)).all()
        if registry_id
    }
    created = 0

    with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            registry_id = (row.get('registry_id') or '').strip()
            name = (row.get('hospital_name') or '').strip()
            state = (row.get('state') or '').strip()
            lga = (row.get('lga') or '').strip()

            if not registry_id or not name or not state or not lga:
                continue
            if registry_id in existing_registry_ids:
                continue

            level = (row.get('facility_level') or '').strip()
            option = (row.get('facility_level_option') or '').strip()
            ownership = (row.get('ownership') or '').strip()
            services, capabilities = _map_services(level, option, ownership)

            db.add(
                Hospital(
                    name=name,
                    country='Nigeria',
                    state=state,
                    lga=lga,
                    address=', '.join(part for part in [lga, state] if part),
                    specialties=option or level or 'General Healthcare',
                    services=services or 'General healthcare services',
                    capabilities=capabilities or 'Basic medical facilities',
                    registry_id=registry_id,
                    phone=None,
                    email=None,
                    latitude=None,
                    longitude=None,
                )
            )
            existing_registry_ids.add(registry_id)
            created += 1

            if created % 2000 == 0:
                db.commit()

    db.commit()
    return created


def _backfill_hospital_coordinates_from_lga_profiles(db: Session) -> int:
    profiles = {
        (profile.state.strip().lower(), profile.lga.strip().lower()): profile
        for profile in db.query(LgaProfile).all()
        if profile.state and profile.lga and profile.centroid_latitude is not None and profile.centroid_longitude is not None
    }
    updated = 0

    hospitals = db.query(Hospital).filter(Hospital.latitude.is_(None), Hospital.longitude.is_(None)).all()
    for hospital in hospitals:
        key = (hospital.state.strip().lower(), hospital.lga.strip().lower())
        profile = profiles.get(key)
        if not profile:
            continue

        seed = hospital.registry_id or hospital.name
        offset = _deterministic_coordinate_offset(seed)
        hospital.latitude = profile.centroid_latitude + offset
        hospital.longitude = profile.centroid_longitude - offset
        updated += 1

    if updated:
        db.commit()
    return updated


def ensure_bootstrap_data() -> None:
    db = SessionLocal()
    try:
        registry_hospital_count = db.query(Hospital).filter(Hospital.registry_id.isnot(None)).count()
        lga_profile_count = db.query(LgaProfile).count()
        capacity_count = db.query(HospitalCapacity).count()

        if registry_hospital_count == 0 and HOSPITAL_CAPACITIES_CSV.exists():
            created = _bootstrap_registry_hospitals_from_capacity_csv(HOSPITAL_CAPACITIES_CSV, db)
            registry_hospital_count += created
            logger.info('Bootstrapped %s registry hospitals from %s', created, HOSPITAL_CAPACITIES_CSV.name)

        if lga_profile_count == 0 and LGA_PROFILES_CSV.exists():
            imported_profiles = import_lga_profiles(LGA_PROFILES_CSV)
            logger.info('Imported %s LGA planning profiles from %s', imported_profiles, LGA_PROFILES_CSV.name)

        missing_coordinates = db.query(Hospital).filter(Hospital.latitude.is_(None), Hospital.longitude.is_(None)).count()
        if missing_coordinates > 0 and db.query(LgaProfile).count() > 0:
            updated_coordinates = _backfill_hospital_coordinates_from_lga_profiles(db)
            logger.info('Backfilled coordinates for %s hospitals from LGA centroids', updated_coordinates)

        if capacity_count == 0 and registry_hospital_count > 0 and HOSPITAL_CAPACITIES_CSV.exists():
            imported_capacities = import_hospital_capacities(HOSPITAL_CAPACITIES_CSV)
            logger.info('Imported %s hospital capacity rows from %s', imported_capacities, HOSPITAL_CAPACITIES_CSV.name)
    except Exception:
        logger.exception('Failed to bootstrap CareMesh data')
        raise
    finally:
        db.close()
