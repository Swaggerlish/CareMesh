from __future__ import annotations

from prepare_nigeria_planning_csvs import GRID3_FEATURE_QUERY_URL, _clean_state_name

import httpx

from app.db.session import SessionLocal
from app.models.hospital import Hospital


def _fetch_features() -> list[dict]:
    features: list[dict] = []
    offset = 0
    with httpx.Client(follow_redirects=True, timeout=180.0) as client:
        while True:
            response = client.get(
                GRID3_FEATURE_QUERY_URL,
                params={
                    'where': '1=1',
                    'outFields': (
                        'facility_name,state,lga,ward,nhfr_facility_code,facility_level,'
                        'facility_level_option,ownership,ownership_type,latitude,longitude'
                    ),
                    'returnGeometry': 'false',
                    'f': 'json',
                    'resultOffset': offset,
                    'resultRecordCount': 2000,
                },
            )
            response.raise_for_status()
            payload = response.json()
            batch = payload.get('features', [])
            if not batch:
                break
            features.extend(batch)
            if not payload.get('exceededTransferLimit'):
                break
            offset += len(batch)
    return features


def _map_services(level: str, option: str) -> tuple[str, str]:
    text = f'{level} {option}'.lower()
    services = ['Consultation']
    capabilities = []

    if 'primary health center' in text or 'primary health clinic' in text:
        services.extend(['Antenatal care', 'Immunization', 'General practice'])
        capabilities.extend(['Outpatient unit', 'Basic maternity'])
    if 'health post' in text:
        services.extend(['Community health outreach', 'Basic triage'])
        capabilities.extend(['Referral point'])
    if 'general hospital' in text or 'secondary' in text:
        services.extend(['Emergency care', 'Inpatient care', 'Surgery'])
        capabilities.extend(['Beds', 'Operating theatre', 'Laboratory'])
    if 'specialized hospital' in text:
        services.extend(['Specialist care', 'Diagnostics'])
        capabilities.extend(['Specialist clinics', 'Advanced laboratory'])
    if 'teaching/tertiary' in text or 'tertiary' in text:
        services.extend(['Specialist care', 'Critical care', 'Surgery'])
        capabilities.extend(['ICU', 'Blood bank', 'Advanced diagnostics'])

    return ', '.join(sorted(set(services))), ', '.join(sorted(set(capabilities)))


def sync_hospitals() -> dict[str, int]:
    features = _fetch_features()
    db = SessionLocal()
    created = 0
    updated = 0
    skipped_duplicates = 0
    try:
        seen_registry_ids: set[str] = set()
        for feature in features:
            attrs = feature['attributes']
            registry_id = (attrs.get('nhfr_facility_code') or '').strip() or None
            name = (attrs.get('facility_name') or '').strip()
            state = _clean_state_name(attrs.get('state') or '')
            lga = (attrs.get('lga') or '').strip()
            ward = (attrs.get('ward') or '').strip()
            level = (attrs.get('facility_level') or '').strip()
            option = (attrs.get('facility_level_option') or '').strip()

            if registry_id:
                if registry_id in seen_registry_ids:
                    skipped_duplicates += 1
                    continue
                seen_registry_ids.add(registry_id)

            hospital = None
            if registry_id:
                hospital = db.query(Hospital).filter(Hospital.registry_id == registry_id).first()
            if not hospital:
                hospital = (
                    db.query(Hospital)
                    .filter(Hospital.name == name, Hospital.state == state, Hospital.lga == lga)
                    .first()
                )

            services, capabilities = _map_services(level, option)
            payload = {
                'name': name,
                'country': 'Nigeria',
                'state': state,
                'lga': lga,
                'address': ', '.join(part for part in [ward, lga, state] if part),
                'specialties': option or level or 'General Healthcare',
                'services': services,
                'capabilities': capabilities or 'Basic medical facilities',
                'registry_id': registry_id,
                'latitude': attrs.get('latitude'),
                'longitude': attrs.get('longitude'),
                'phone': None,
                'email': None,
            }

            if hospital:
                for key, value in payload.items():
                    setattr(hospital, key, value)
                updated += 1
            else:
                db.add(Hospital(**payload))
                created += 1

            if (created + updated) % 2000 == 0:
                db.commit()

        db.commit()
        return {
            'created': created,
            'updated': updated,
            'skipped_duplicates': skipped_duplicates,
            'total_features': len(features),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    result = sync_hospitals()
    print(result)
