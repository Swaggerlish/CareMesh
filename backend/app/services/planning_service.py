from __future__ import annotations

from collections import defaultdict
from math import atan2, cos, radians, sin, sqrt

from sqlalchemy.orm import Session, joinedload

from app.models.hospital import Hospital
from app.models.lga_profile import LgaProfile

CORE_SERVICE_RULES = [
    ('Emergency Care', ['emergency', 'accident', 'trauma']),
    ('Surgery', ['surgery', 'surgical', 'operating']),
    ('ICU', ['icu', 'intensive care']),
    ('Maternity', ['maternity', 'obstetric', 'antenatal', 'labour']),
    ('Pediatrics', ['pediatric', 'paediatric', 'children', 'neonatal']),
    ('Diagnostics', ['diagnostic', 'laboratory', 'radiology', 'x-ray', 'scan']),
]
def _parse_service_text(hospital: Hospital) -> str:
    return ' '.join(
        value for value in [hospital.specialties, hospital.services, hospital.capabilities] if value
    ).lower()


def _normalize_admin_name(value: str) -> str:
    normalized = (value or '').strip().lower()
    for token in ['-', '/', '&', ',', '.', '(', ')']:
        normalized = normalized.replace(token, ' ')
    return ' '.join(normalized.split())


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    a = sin(d_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c


def _infer_capacity(hospital: Hospital) -> dict[str, int]:
    profile = hospital.capacity_profile
    if profile:
        return {
            'beds': profile.bed_count or 0,
            'doctors': profile.doctor_count or 0,
            'nurses': profile.nurse_count or 0,
            'ambulances': profile.ambulance_count or 0,
        }

    text = _parse_service_text(hospital)
    base_beds = 8
    base_doctors = 2
    base_nurses = 4

    if 'hospital' in text:
        base_beds += 22
        base_doctors += 4
        base_nurses += 8
    if 'tertiary' in text or 'teaching' in text:
        base_beds += 70
        base_doctors += 18
        base_nurses += 28
    elif 'secondary' in text:
        base_beds += 35
        base_doctors += 10
        base_nurses += 16
    elif 'primary' in text or 'clinic' in text or 'health centre' in text:
        base_beds += 10
        base_doctors += 2
        base_nurses += 6

    return {
        'beds': base_beds,
        'doctors': base_doctors,
        'nurses': base_nurses,
        'ambulances': 1 if 'emergency' in text else 0,
    }


def _infer_profile_population(facility_count: int, total_beds: int) -> int:
    return 25000 + facility_count * 18000 + total_beds * 120


def _estimate_travel_minutes(distance_km: float, profile: LgaProfile | None) -> int:
    base_speed = profile.average_road_speed_kph if profile and profile.average_road_speed_kph else 42.0
    road_factor = profile.road_access_factor if profile and profile.road_access_factor else 1.15
    rurality = profile.rurality_index if profile and profile.rurality_index else 1.0
    effective_speed = max(18.0, base_speed / max(0.4, road_factor * rurality))
    return round((distance_km / effective_speed) * 60)


def _recommendation(missing_services: list[str], population: int | None, travel_minutes: int) -> str:
    if 'Emergency Care' in missing_services or travel_minutes >= 150:
        return 'Prioritize emergency stabilization unit, ambulance support, and rapid referral funding.'
    if population and population >= 150000:
        return 'Expand bed space, diagnostics, and clinical staffing in the nearest public facility.'
    if 'Maternity' in missing_services or 'Pediatrics' in missing_services:
        return 'Deploy maternal and child health resources with outreach staff and essential medicines.'
    return 'Target specialist outreach, diagnostics, and routine service support for this LGA.'


def build_planning_snapshot(db: Session, state: str | None = None, lga: str | None = None) -> dict:
    all_hospitals_with_coordinates = db.query(Hospital).filter(
        Hospital.registry_id.isnot(None),
        Hospital.latitude.isnot(None),
        Hospital.longitude.isnot(None)
    ).all()

    query = db.query(Hospital).options(joinedload(Hospital.capacity_profile)).filter(Hospital.registry_id.isnot(None))
    if state:
        query = query.filter(Hospital.state == state)
    if lga:
        query = query.filter(Hospital.lga == lga)
    hospitals = query.order_by(Hospital.state.asc(), Hospital.lga.asc(), Hospital.name.asc()).all()

    profiles = db.query(LgaProfile)
    if state:
        profiles = profiles.filter(LgaProfile.state == state)
    if lga:
        profiles = profiles.filter(LgaProfile.lga == lga)
    profile_map = {
        (_normalize_admin_name(item.state), _normalize_admin_name(item.lga)): item
        for item in profiles.all()
    }

    grouped: dict[tuple[str, str], list[Hospital]] = defaultdict(list)
    for hospital in hospitals:
        grouped[(hospital.state, hospital.lga)].append(hospital)

    deserts = []
    for (item_state, item_lga), facilities in grouped.items():
        mapped = [item for item in facilities if item.latitude is not None and item.longitude is not None]
        centroid_lat = sum(item.latitude for item in mapped) / len(mapped) if mapped else None
        centroid_lon = sum(item.longitude for item in mapped) / len(mapped) if mapped else None

        covered_services: set[str] = set()
        total_beds = 0
        total_doctors = 0
        total_nurses = 0
        for facility in facilities:
            text = _parse_service_text(facility)
            for label, keywords in CORE_SERVICE_RULES:
                if any(keyword in text for keyword in keywords):
                    covered_services.add(label)
            capacity = _infer_capacity(facility)
            total_beds += capacity['beds']
            total_doctors += capacity['doctors']
            total_nurses += capacity['nurses']

        missing_services = [label for label, _ in CORE_SERVICE_RULES if label not in covered_services]
        profile = profile_map.get((_normalize_admin_name(item_state), _normalize_admin_name(item_lga)))
        population = profile.population if profile and profile.population else _infer_profile_population(len(facilities), total_beds)
        population_source = profile.source if profile and profile.population else 'heuristic'

        nearest_care_km = 0
        if centroid_lat is not None and centroid_lon is not None:
            nearest = None
            for hospital in all_hospitals_with_coordinates:
                if hospital.state == item_state and hospital.lga == item_lga:
                    continue
                distance = _haversine_km(centroid_lat, centroid_lon, hospital.latitude, hospital.longitude)
                if nearest is None or distance < nearest:
                    nearest = distance
            nearest_care_km = round(nearest or 0)

        if profile and profile.nearest_care_km is not None:
            nearest_care_km = round(profile.nearest_care_km)
        if profile and profile.estimated_travel_time_minutes is not None:
            travel_minutes = profile.estimated_travel_time_minutes
        else:
            travel_minutes = _estimate_travel_minutes(nearest_care_km, profile)
        scarcity_score = max(0, 3 - len(facilities)) * 14
        capacity_score = 0
        if population:
            if total_beds < population / 5000:
                capacity_score += 16
            if total_doctors < population / 12000:
                capacity_score += 18
            if total_nurses < population / 5000:
                capacity_score += 10
        service_score = len(missing_services) * 10
        travel_score = min(35, round(travel_minutes / 8))
        score = scarcity_score + capacity_score + service_score + travel_score

        severity = 'WATCHLIST'
        if score >= 78:
            severity = 'CRITICAL GAP'
        elif score >= 52:
            severity = 'SERVICE GAP'

        deserts.append(
            {
                'state': item_state,
                'lga': item_lga,
                'severity': severity,
                'score': score,
                'population': population,
                'population_source': population_source,
                'nearest_care_km': nearest_care_km,
                'estimated_travel_time_minutes': travel_minutes,
                'facilities_in_lga': len(facilities),
                'mapped_hospitals': len(mapped),
                'bed_capacity': total_beds,
                'doctor_capacity': total_doctors,
                'nurse_capacity': total_nurses,
                'missing_services': missing_services,
                'recommendation': _recommendation(missing_services, population, travel_minutes),
            }
        )

    deserts = [item for item in deserts if item['severity'] in {'CRITICAL GAP', 'SERVICE GAP', 'WATCHLIST'}]
    deserts.sort(key=lambda item: item['score'], reverse=True)

    inventory_totals: dict[str, dict] = {}
    for desert in deserts:
        for service in desert['missing_services']:
            current = inventory_totals.get(service, {'service': service, 'desert_count': 0, 'affected_population': 0})
            current['desert_count'] += 1
            current['affected_population'] += desert['population'] or 0
            inventory_totals[service] = current

    facility_summary: dict[str, dict] = {}
    for hospital in hospitals:
        current = facility_summary.get(
            hospital.state,
            {'state': hospital.state, 'count': 0, 'mapped': 0, 'total_beds': 0, 'total_doctors': 0, 'specialties': set()},
        )
        current['count'] += 1
        if hospital.latitude is not None and hospital.longitude is not None:
            current['mapped'] += 1
        capacity = _infer_capacity(hospital)
        current['total_beds'] += capacity['beds']
        current['total_doctors'] += capacity['doctors']
        for specialty in [item.strip() for item in hospital.specialties.split(',') if item.strip()]:
            if len(current['specialties']) < 6:
                current['specialties'].add(specialty)
        facility_summary[hospital.state] = current

    facilities_summary_list = [
        {**item, 'specialties': sorted(item['specialties'])}
        for item in facility_summary.values()
    ]
    facilities_summary_list.sort(key=lambda item: item['count'], reverse=True)

    note = (
        'Planning scores combine mapped hospitals, imported LGA population profiles, nearest-care travel times, '
        'and hospital capacity. Where imported route or capacity data is missing, the API falls back to heuristics.'
    )

    return {
        'medical_deserts': deserts[:12],
        'inventory_signals': sorted(inventory_totals.values(), key=lambda item: item['affected_population'], reverse=True)[:8],
        'facilities_summary': facilities_summary_list[:8],
        'note': note,
    }
