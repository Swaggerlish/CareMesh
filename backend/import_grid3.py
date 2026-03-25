import csv
import httpx
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models.hospital import Hospital

GRID3_CSV_URL = 'https://data.humdata.org/dataset/81c68cba-93e8-4c37-8a68-0088328ea577/resource/3b3a4e5b-6b3c-4b3a-8b3a-3b3a4e5b6b3c/download/health_facilities.csv'  # Note: Verify this URL as it may change

def download_csv(url):
    response = httpx.get(url)
    response.raise_for_status()
    return response.text

def parse_csv(csv_text):
    reader = csv.DictReader(csv_text.splitlines())
    return list(reader)

def map_to_hospital(row):
    # Map GRID3 columns to our model
    facility_type = row.get('facility_type', '').lower()
    ownership = row.get('ownership', '').lower()
    
    # Infer services and capabilities from facility_type
    services = []
    capabilities = []
    
    if 'hospital' in facility_type:
        services.extend(['Consultation', 'Emergency response', 'Inpatient care'])
        capabilities.extend(['Beds', 'Pharmacy'])
    if 'clinic' in facility_type or 'health centre' in facility_type:
        services.extend(['Consultation', 'Vaccination', 'Antenatal care'])
        capabilities.extend(['Basic laboratory'])
    if 'primary' in facility_type:
        services.extend(['General practice', 'Maternity care'])
    if 'secondary' in facility_type or 'tertiary' in facility_type:
        services.extend(['Specialized care', 'Surgery'])
        capabilities.extend(['Advanced laboratory', 'Radiology'])
    if 'dispensary' in facility_type:
        services.extend(['Basic healthcare', 'Drug dispensing'])
    
    # Ownership might indicate capabilities
    if 'private' in ownership:
        capabilities.append('Private facilities')
    if 'public' in ownership:
        capabilities.append('Government facilities')
    
    return {
        'name': row.get('facility_name', ''),
        'country': 'Nigeria',
        'state': row.get('state', ''),
        'lga': row.get('lga', ''),  # LGA as lga
        'address': f"{row.get('ward', '')}, {row.get('lga', '')}, {row.get('state', '')}".strip(', '),
        'specialties': row.get('facility_type', 'General Healthcare'),
        'services': ', '.join(set(services)) if services else 'General healthcare services',
        'capabilities': ', '.join(set(capabilities)) if capabilities else 'Basic medical facilities',
        'registry_id': row.get('facility_id', None),
        'latitude': float(row.get('latitude', 0)) if row.get('latitude') and row.get('latitude') != '' else None,
        'longitude': float(row.get('longitude', 0)) if row.get('longitude') and row.get('longitude') != '' else None,
        'phone': None,
        'email': None,
    }

def import_hospitals():
    print("Downloading GRID3 dataset...")
    csv_text = download_csv(GRID3_CSV_URL)
    rows = parse_csv(csv_text)
    print(f"Downloaded {len(rows)} facilities.")
    
    db = SessionLocal()
    try:
        existing_registry_ids = {h.registry_id for h in db.query(Hospital.registry_id).filter(Hospital.registry_id.isnot(None)).all()}
        count = 0
        for row in rows:
            hospital_data = map_to_hospital(row)
            if hospital_data['registry_id'] and hospital_data['registry_id'] not in existing_registry_ids:
                db.add(Hospital(**hospital_data))
                existing_registry_ids.add(hospital_data['registry_id'])
                count += 1
                if count % 1000 == 0:
                    db.commit()
                    print(f"Imported {count} hospitals...")
        db.commit()
        print(f"Successfully imported {count} new hospitals from GRID3 dataset.")
    except Exception as e:
        print(f"Error importing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    import_hospitals()