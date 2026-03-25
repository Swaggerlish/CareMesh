from __future__ import annotations

import csv
import io
import json
import math
import tempfile
import zipfile
from pathlib import Path

import httpx
import shapefile

WORLDPOP_ADMIN_ZIP_URL = 'https://data.worldpop.org/repo/wopr/NGA/population/v2.0/NGA_population_v2_0_admin.zip'
GRID3_FEATURE_QUERY_URL = (
    'https://services3.arcgis.com/BU6Aadhn6tbBEdyk/ArcGIS/rest/services/'
    'GRID3_NGA_health_facilities_v2_0/FeatureServer/0/query'
)
OSRM_TABLE_URL = 'https://router.project-osrm.org/table/v1/driving/'

OUTPUT_DIR = Path(__file__).parent / 'data' / 'planning'
LGA_OUTPUT = OUTPUT_DIR / 'lga_profiles_nigeria_worldpop_v2.csv'
CAPACITY_OUTPUT = OUTPUT_DIR / 'hospital_capacities_nigeria_grid3_baseline.csv'


LEVEL_BASELINES = {
    'Teaching/Tertiary Hospital': {
        'bed_count': 250,
        'doctor_count': 80,
        'nurse_count': 180,
        'ambulance_count': 6,
        'has_emergency_unit': True,
        'has_operating_theatre': True,
        'has_icu': True,
        'has_blood_bank': True,
    },
    'Specialized Hospital': {
        'bed_count': 120,
        'doctor_count': 35,
        'nurse_count': 90,
        'ambulance_count': 4,
        'has_emergency_unit': True,
        'has_operating_theatre': True,
        'has_icu': True,
        'has_blood_bank': True,
    },
    'General Hospital': {
        'bed_count': 80,
        'doctor_count': 20,
        'nurse_count': 55,
        'ambulance_count': 3,
        'has_emergency_unit': True,
        'has_operating_theatre': True,
        'has_icu': False,
        'has_blood_bank': True,
    },
    'Primary Health Center': {
        'bed_count': 12,
        'doctor_count': 2,
        'nurse_count': 8,
        'ambulance_count': 1,
        'has_emergency_unit': True,
        'has_operating_theatre': False,
        'has_icu': False,
        'has_blood_bank': False,
    },
    'Primary Health Clinic': {
        'bed_count': 6,
        'doctor_count': 1,
        'nurse_count': 4,
        'ambulance_count': 0,
        'has_emergency_unit': False,
        'has_operating_theatre': False,
        'has_icu': False,
        'has_blood_bank': False,
    },
    'Health Post': {
        'bed_count': 0,
        'doctor_count': 0,
        'nurse_count': 2,
        'ambulance_count': 0,
        'has_emergency_unit': False,
        'has_operating_theatre': False,
        'has_icu': False,
        'has_blood_bank': False,
    },
    'Unknown': {
        'bed_count': 4,
        'doctor_count': 1,
        'nurse_count': 2,
        'ambulance_count': 0,
        'has_emergency_unit': False,
        'has_operating_theatre': False,
        'has_icu': False,
        'has_blood_bank': False,
    },
}

STATE_TRAVEL_DEFAULTS = {
    'Abia': (38.0, 1.08, 1.02),
    'Adamawa': (34.0, 1.2, 1.18),
    'Akwa Ibom': (36.0, 1.08, 1.0),
    'Anambra': (39.0, 1.04, 0.98),
    'Bauchi': (33.0, 1.18, 1.14),
    'Bayelsa': (28.0, 1.35, 1.22),
    'Benue': (34.0, 1.16, 1.1),
    'Borno': (30.0, 1.34, 1.28),
    'Cross River': (31.0, 1.28, 1.16),
    'Delta': (34.0, 1.16, 1.08),
    'Ebonyi': (35.0, 1.14, 1.08),
    'Edo': (36.0, 1.1, 1.02),
    'Ekiti': (38.0, 1.06, 0.98),
    'Enugu': (37.0, 1.08, 1.0),
    'Federal Capital Territory': (40.0, 1.0, 0.92),
    'Gombe': (35.0, 1.14, 1.08),
    'Imo': (38.0, 1.06, 0.98),
    'Jigawa': (33.0, 1.16, 1.12),
    'Kaduna': (36.0, 1.12, 1.04),
    'Kano': (35.0, 1.12, 1.04),
    'Katsina': (33.0, 1.16, 1.1),
    'Kebbi': (33.0, 1.18, 1.14),
    'Kogi': (35.0, 1.14, 1.08),
    'Kwara': (36.0, 1.1, 1.02),
    'Lagos': (42.0, 0.98, 0.9),
    'Nasarawa': (35.0, 1.14, 1.08),
    'Niger': (34.0, 1.18, 1.14),
    'Ogun': (39.0, 1.02, 0.96),
    'Ondo': (36.0, 1.1, 1.02),
    'Osun': (38.0, 1.04, 0.98),
    'Oyo': (38.0, 1.04, 0.98),
    'Plateau': (34.0, 1.2, 1.1),
    'Rivers': (32.0, 1.22, 1.1),
    'Sokoto': (33.0, 1.16, 1.12),
    'Taraba': (31.0, 1.28, 1.2),
    'Yobe': (32.0, 1.22, 1.18),
    'Zamfara': (33.0, 1.16, 1.14),
}


def _clean_state_name(value: str) -> str:
    text = (value or '').strip()
    return 'Federal Capital Territory' if text in {'FCT', 'Abuja Federal Capital Territory'} else text


def _travel_defaults_for_state(state: str) -> tuple[float, float, float]:
    return STATE_TRAVEL_DEFAULTS.get(state, (35.0, 1.12, 1.05))


def _normalize_admin_name(value: str) -> str:
    normalized = _clean_state_name(value).strip().lower()
    for token in ['-', '/', '&', ',', '.', '(', ')']:
        normalized = normalized.replace(token, ' ')
    return ' '.join(normalized.split())


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


def _polygon_centroid(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    if len(points) < 3:
        return None

    area_twice = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for index in range(len(points) - 1):
        x1, y1 = points[index]
        x2, y2 = points[index + 1]
        cross = (x1 * y2) - (x2 * y1)
        area_twice += cross
        centroid_x += (x1 + x2) * cross
        centroid_y += (y1 + y2) * cross

    if abs(area_twice) < 1e-12:
        avg_x = sum(point[0] for point in points) / len(points)
        avg_y = sum(point[1] for point in points) / len(points)
        return avg_x, avg_y

    area = area_twice / 2
    return centroid_x / (6 * area), centroid_y / (6 * area)


def _shape_centroid(shape) -> tuple[float, float] | None:
    parts = list(shape.parts) + [len(shape.points)]
    weighted_x = 0.0
    weighted_y = 0.0
    total_weight = 0.0

    for index in range(len(parts) - 1):
        ring = shape.points[parts[index]:parts[index + 1]]
        if ring and ring[0] != ring[-1]:
            ring = ring + [ring[0]]

        centroid = _polygon_centroid(ring)
        if centroid is None:
            continue

        ring_area = 0.0
        for point_index in range(len(ring) - 1):
            x1, y1 = ring[point_index]
            x2, y2 = ring[point_index + 1]
            ring_area += (x1 * y2) - (x2 * y1)
        ring_area = abs(ring_area / 2)
        if ring_area == 0:
            ring_area = 1.0

        weighted_x += centroid[0] * ring_area
        weighted_y += centroid[1] * ring_area
        total_weight += ring_area

    if total_weight == 0:
        return None
    return weighted_x / total_weight, weighted_y / total_weight


def _fetch_worldpop_level2_rows(client: httpx.Client) -> list[dict[str, str]]:
    response = client.get(WORLDPOP_ADMIN_ZIP_URL, timeout=180.0)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        with archive.open('NGA_population_v2_0_admin_level2.csv') as handle:
            content = handle.read().decode('utf-8-sig')
    return list(csv.DictReader(io.StringIO(content)))


def _fetch_worldpop_level2_centroids(client: httpx.Client) -> dict[tuple[str, str], tuple[float, float]]:
    response = client.get(WORLDPOP_ADMIN_ZIP_URL, timeout=180.0)
    response.raise_for_status()
    centroids: dict[tuple[str, str], tuple[float, float]] = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for member in archive.namelist():
                if member.startswith('NGA_population_v2_0_admin_level2_boundaries.'):
                    archive.extract(member, temp_path)

        reader = shapefile.Reader(str(temp_path / 'NGA_population_v2_0_admin_level2_boundaries.shp'))
        try:
            fields = [field[0] for field in reader.fields[1:]]
            for shape_record in reader.iterShapeRecords():
                record = dict(zip(fields, shape_record.record))
                key = (_normalize_admin_name(record.get('state', '')), _normalize_admin_name(record.get('local', '')))
                centroid = _shape_centroid(shape_record.shape)
                if centroid:
                    centroids[key] = (round(centroid[1], 6), round(centroid[0], 6))
        finally:
            reader.close()

    return centroids


def _fetch_grid3_facilities(client: httpx.Client) -> list[dict]:
    features: list[dict] = []
    offset = 0
    while True:
        response = client.get(
            GRID3_FEATURE_QUERY_URL,
            params={
                'where': '1=1',
                'outFields': 'facility_name,state,lga,nhfr_facility_code,facility_level,facility_level_option,ownership,ownership_type,latitude,longitude',
                'returnGeometry': 'false',
                'f': 'json',
                'resultOffset': offset,
                'resultRecordCount': 2000,
            },
            timeout=180.0,
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


def _route_to_nearest_hospital(
    client: httpx.Client,
    state: str,
    lga: str,
    centroid_lat: float,
    centroid_lon: float,
    facility_features: list[dict],
    candidate_count: int = 8,
) -> dict[str, str | float | int | None]:
    normalized_state = _normalize_admin_name(state)
    normalized_lga = _normalize_admin_name(lga)
    candidates = []

    for feature in facility_features:
        attributes = feature['attributes']
        latitude = attributes.get('latitude')
        longitude = attributes.get('longitude')
        if latitude is None or longitude is None:
            continue

        if (
            _normalize_admin_name(attributes.get('state', '')) == normalized_state
            and _normalize_admin_name(attributes.get('lga', '')) == normalized_lga
        ):
            continue

        distance = _haversine_km(centroid_lat, centroid_lon, latitude, longitude)
        candidates.append((distance, attributes))

    candidates.sort(key=lambda item: item[0])
    top_candidates = candidates[:candidate_count]
    if not top_candidates:
        return {
            'nearest_hospital_registry_id': None,
            'nearest_hospital_name': None,
            'nearest_care_km': None,
            'estimated_travel_time_minutes': None,
            'route_source': 'missing-candidates',
        }

    coordinates = [f'{centroid_lon},{centroid_lat}'] + [
        f"{candidate['longitude']},{candidate['latitude']}" for _, candidate in top_candidates
    ]
    try:
        response = client.get(
            OSRM_TABLE_URL + ';'.join(coordinates),
            params={
                'annotations': 'duration,distance',
                'sources': '0',
                'destinations': ';'.join(str(index) for index in range(1, len(coordinates))),
            },
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        durations = payload.get('durations', [[]])[0]
        distances = payload.get('distances', [[]])[0]
    except httpx.HTTPError:
        durations = []
        distances = []

    best_index = None
    best_duration = None
    for index, duration in enumerate(durations):
        if duration is None:
            continue
        if best_duration is None or duration < best_duration:
            best_duration = duration
            best_index = index

    if best_index is None:
        fallback_distance, fallback_candidate = top_candidates[0]
        speed, access, rurality = _travel_defaults_for_state(state)
        effective_speed = max(18.0, speed / max(0.4, access * rurality))
        return {
            'nearest_hospital_registry_id': (fallback_candidate.get('nhfr_facility_code') or '').strip() or None,
            'nearest_hospital_name': (fallback_candidate.get('facility_name') or '').strip() or None,
            'nearest_care_km': round(fallback_distance, 2),
            'estimated_travel_time_minutes': round((fallback_distance / effective_speed) * 60),
            'route_source': 'OSRM fallback to haversine proxy',
        }

    best_candidate = top_candidates[best_index][1]
    return {
        'nearest_hospital_registry_id': (best_candidate.get('nhfr_facility_code') or '').strip() or None,
        'nearest_hospital_name': (best_candidate.get('facility_name') or '').strip() or None,
        'nearest_care_km': round((distances[best_index] or 0) / 1000, 2),
        'estimated_travel_time_minutes': round((best_duration or 0) / 60),
        'route_source': 'OSRM public routing table from WorldPop LGA centroid',
    }


def _write_lga_profiles(
    rows: list[dict[str, str]],
    centroids: dict[tuple[str, str], tuple[float, float]],
) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with LGA_OUTPUT.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'state',
                'lga',
                'population',
                'centroid_latitude',
                'centroid_longitude',
                'nearest_hospital_registry_id',
                'nearest_hospital_name',
                'nearest_care_km',
                'estimated_travel_time_minutes',
                'average_road_speed_kph',
                'road_access_factor',
                'rurality_index',
                'route_source',
                'source',
            ],
        )
        writer.writeheader()
        for row in rows:
            state = _clean_state_name(row['state'])
            lga = row['local'].strip()
            speed, access, rurality = _travel_defaults_for_state(state)
            centroid = centroids.get((_normalize_admin_name(state), _normalize_admin_name(lga)))

            writer.writerow(
                {
                    'state': state,
                    'lga': lga,
                    'population': round(float(row['mean'])),
                    'centroid_latitude': centroid[0] if centroid else None,
                    'centroid_longitude': centroid[1] if centroid else None,
                    'nearest_hospital_registry_id': None,
                    'nearest_hospital_name': None,
                    'nearest_care_km': None,
                    'estimated_travel_time_minutes': None,
                    'average_road_speed_kph': speed,
                    'road_access_factor': access,
                    'rurality_index': rurality,
                    'route_source': 'pending-osrm-cache',
                    'source': 'WorldPop v2.0 mean population',
                }
            )
    return len(rows)


def _baseline_for_feature(attributes: dict) -> dict:
    option = (attributes.get('facility_level_option') or '').strip() or 'Unknown'
    level = (attributes.get('facility_level') or '').strip()
    baseline = LEVEL_BASELINES.get(option, LEVEL_BASELINES['Unknown']).copy()

    if level == 'Tertiary' and option != 'Teaching/Tertiary Hospital':
        baseline['bed_count'] = max(baseline['bed_count'], 180)
        baseline['doctor_count'] = max(baseline['doctor_count'], 40)
        baseline['nurse_count'] = max(baseline['nurse_count'], 110)
        baseline['ambulance_count'] = max(baseline['ambulance_count'], 4)
        baseline['has_icu'] = True
    elif level == 'Secondary' and option not in {'General Hospital', 'Specialized Hospital'}:
        baseline['bed_count'] = max(baseline['bed_count'], 45)
        baseline['doctor_count'] = max(baseline['doctor_count'], 10)
        baseline['nurse_count'] = max(baseline['nurse_count'], 24)
        baseline['ambulance_count'] = max(baseline['ambulance_count'], 2)
        baseline['has_emergency_unit'] = True
        baseline['has_operating_theatre'] = True

    ownership_type = (attributes.get('ownership_type') or '').lower()
    if 'federal' in ownership_type:
        baseline['bed_count'] = round(baseline['bed_count'] * 1.15)
        baseline['doctor_count'] = round(baseline['doctor_count'] * 1.2)
        baseline['nurse_count'] = round(baseline['nurse_count'] * 1.15)
    elif 'state' in ownership_type:
        baseline['bed_count'] = round(baseline['bed_count'] * 1.05)
        baseline['doctor_count'] = round(baseline['doctor_count'] * 1.08)
        baseline['nurse_count'] = round(baseline['nurse_count'] * 1.06)

    return baseline


def _write_capacity_baseline(features: list[dict]) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with CAPACITY_OUTPUT.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'registry_id',
                'hospital_name',
                'state',
                'lga',
                'facility_level',
                'facility_level_option',
                'ownership',
                'ownership_type',
                'bed_count',
                'doctor_count',
                'nurse_count',
                'ambulance_count',
                'has_emergency_unit',
                'has_operating_theatre',
                'has_icu',
                'has_blood_bank',
                'source',
            ],
        )
        writer.writeheader()
        for feature in features:
            attributes = feature['attributes']
            baseline = _baseline_for_feature(attributes)
            writer.writerow(
                {
                    'registry_id': (attributes.get('nhfr_facility_code') or '').strip(),
                    'hospital_name': (attributes.get('facility_name') or '').strip(),
                    'state': _clean_state_name(attributes.get('state') or ''),
                    'lga': (attributes.get('lga') or '').strip(),
                    'facility_level': (attributes.get('facility_level') or '').strip(),
                    'facility_level_option': (attributes.get('facility_level_option') or '').strip(),
                    'ownership': (attributes.get('ownership') or '').strip(),
                    'ownership_type': (attributes.get('ownership_type') or '').strip(),
                    **baseline,
                    'source': 'GRID3/NHFR 2024 facility level with capacity baseline proxy',
                }
            )
    return len(features)


def main() -> None:
    with httpx.Client(follow_redirects=True) as client:
        lga_rows = _fetch_worldpop_level2_rows(client)
        lga_centroids = _fetch_worldpop_level2_centroids(client)
        facility_features = _fetch_grid3_facilities(client)

    lga_count = _write_lga_profiles(lga_rows, lga_centroids)
    facility_count = _write_capacity_baseline(facility_features)

    print(
        json.dumps(
            {
                'lga_profiles_csv': str(LGA_OUTPUT),
                'lga_rows': lga_count,
                'hospital_capacities_csv': str(CAPACITY_OUTPUT),
                'facility_rows': facility_count,
            },
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
