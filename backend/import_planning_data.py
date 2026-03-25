from __future__ import annotations

import csv
from pathlib import Path

from app.db.session import SessionLocal
from app.models.hospital import Hospital
from app.models.hospital_capacity import HospitalCapacity
from app.models.lga_profile import LgaProfile


def _to_int(value: str | None) -> int | None:
    if value in (None, ''):
        return None
    try:
        return int(float(str(value).strip().replace(',', '')))
    except (TypeError, ValueError):
        return None


def _to_float(value: str | None) -> float | None:
    if value in (None, ''):
        return None
    try:
        return float(str(value).strip().replace(',', ''))
    except (TypeError, ValueError):
        return None


def _to_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


def import_lga_profiles(csv_path: Path) -> int:
    db = SessionLocal()
    count = 0
    try:
        profile_cache: dict[tuple[str, str], LgaProfile] = {
            (profile.state, profile.lga): profile
            for profile in db.query(LgaProfile).all()
        }
        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                state = (row.get('state') or '').strip()
                lga = (row.get('lga') or '').strip()
                if not state or not lga:
                    continue

                key = (state, lga)
                profile = profile_cache.get(key)
                if not profile:
                    profile = LgaProfile(state=state, lga=lga)
                    db.add(profile)
                    profile_cache[key] = profile

                profile.population = _to_int(row.get('population'))
                profile.centroid_latitude = _to_float(row.get('centroid_latitude'))
                profile.centroid_longitude = _to_float(row.get('centroid_longitude'))
                profile.nearest_hospital_registry_id = row.get('nearest_hospital_registry_id') or None
                profile.nearest_hospital_name = row.get('nearest_hospital_name') or None
                profile.nearest_care_km = _to_float(row.get('nearest_care_km'))
                profile.estimated_travel_time_minutes = _to_int(row.get('estimated_travel_time_minutes'))
                profile.average_road_speed_kph = _to_float(row.get('average_road_speed_kph'))
                profile.road_access_factor = _to_float(row.get('road_access_factor'))
                profile.rurality_index = _to_float(row.get('rurality_index'))
                profile.route_source = row.get('route_source') or None
                profile.source = row.get('source') or 'manual-import'
                count += 1

        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def import_hospital_capacities(csv_path: Path) -> int:
    db = SessionLocal()
    count = 0
    try:
        seen_hospital_ids: set[int] = set()
        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                registry_id = (row.get('registry_id') or '').strip()
                hospital_name = (row.get('hospital_name') or '').strip()
                hospital = None

                if registry_id:
                    hospital = db.query(Hospital).filter(Hospital.registry_id == registry_id).first()
                if not hospital and hospital_name:
                    hospital = db.query(Hospital).filter(Hospital.name == hospital_name).first()
                if not hospital:
                    continue

                if hospital.id in seen_hospital_ids:
                    continue
                seen_hospital_ids.add(hospital.id)

                capacity = hospital.capacity_profile
                if not capacity:
                    capacity = HospitalCapacity(hospital_id=hospital.id)
                    db.add(capacity)

                capacity.bed_count = _to_int(row.get('bed_count'))
                capacity.doctor_count = _to_int(row.get('doctor_count'))
                capacity.nurse_count = _to_int(row.get('nurse_count'))
                capacity.ambulance_count = _to_int(row.get('ambulance_count'))
                capacity.has_emergency_unit = _to_bool(row.get('has_emergency_unit'))
                capacity.has_operating_theatre = _to_bool(row.get('has_operating_theatre'))
                capacity.has_icu = _to_bool(row.get('has_icu'))
                capacity.has_blood_bank = _to_bool(row.get('has_blood_bank'))
                count += 1

        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import planning datasets for CareMesh.')
    parser.add_argument('--lga-profiles', type=Path, help='CSV with state,lga,population,average_road_speed_kph,road_access_factor,rurality_index,source')
    parser.add_argument('--hospital-capacities', type=Path, help='CSV with registry_id or hospital_name plus capacity columns')
    args = parser.parse_args()

    if args.lga_profiles:
        print(f'Imported {import_lga_profiles(args.lga_profiles)} LGA profiles')
    if args.hospital_capacities:
        print(f'Imported {import_hospital_capacities(args.hospital_capacities)} hospital capacity rows')
