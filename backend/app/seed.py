from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.hospital import Hospital

state_lga_pairs = [
    ('Abia', 'Umuahia'),
    ('Abia', 'Aba North'),
    ('Abia', 'Aba South'),
    ('Adamawa', 'Yola North'),
    ('Adamawa', 'Yola South'),
    ('Adamawa', 'Mubi North'),
    ('Akwa Ibom', 'Uyo'),
    ('Akwa Ibom', 'Eket'),
    ('Akwa Ibom', 'Ikot Ekpene'),
    ('Anambra', 'Awka South'),
    ('Anambra', 'Awka North'),
    ('Anambra', 'Onitsha North'),
    ('Bauchi', 'Bauchi'),
    ('Bauchi', 'Katagum'),
    ('Bauchi', 'Misau'),
    ('Bayelsa', 'Yenagoa'),
    ('Bayelsa', 'Southern Ijaw'),
    ('Bayelsa', 'Brass'),
    ('Benue', 'Makurdi'),
    ('Benue', 'Gboko'),
    ('Benue', 'Otukpo'),
    ('Borno', 'Maiduguri'),
    ('Borno', 'Jere'),
    ('Borno', 'Konduga'),
    ('Cross River', 'Calabar South'),
    ('Cross River', 'Calabar Municipality'),
    ('Cross River', 'Odukpani'),
    ('Delta', 'Asaba'),
    ('Delta', 'Warri North'),
    ('Delta', 'Warri South'),
    ('Ebonyi', 'Abakaliki'),
    ('Ebonyi', 'Ebonyi'),
    ('Ebonyi', 'Ivo'),
    ('Edo', 'Benin City'),
    ('Edo', 'Egor'),
    ('Edo', 'Oredo'),
    ('Ekiti', 'Ado Ekiti'),
    ('Ekiti', 'Ekiti South-West'),
    ('Ekiti', 'Ekiti West'),
    ('Enugu', 'Enugu North'),
    ('Enugu', 'Enugu South'),
    ('Enugu', 'Nsukka'),
    ('FCT', 'Abuja Municipal'),
    ('FCT', 'Bwari'),
    ('FCT', 'Kuje'),
    ('Gombe', 'Gombe'),
    ('Gombe', 'Akko'),
    ('Gombe', 'Yamaltu/Deba'),
    ('Imo', 'Owerri'),
    ('Imo', 'Owerri North'),
    ('Imo', 'Orlu'),
    ('Jigawa', 'Dutse'),
    ('Jigawa', 'Hadejia'),
    ('Jigawa', 'Kazaure'),
    ('Kaduna', 'Kaduna North'),
    ('Kaduna', 'Kaduna South'),
    ('Kaduna', 'Zaria'),
    ('Kano', 'Kano Municipal'),
    ('Kano', 'Kano North'),
    ('Kano', 'Kano South'),
    ('Katsina', 'Katsina'),
    ('Katsina', 'Daura'),
    ('Katsina', 'Funtua'),
    ('Kebbi', 'Birnin Kebbi'),
    ('Kebbi', 'Argungu'),
    ('Kebbi', 'Yauri'),
    ('Kogi', 'Lokoja'),
    ('Kogi', 'Kogi'),
    ('Kogi', 'Ankpa'),
    ('Kwara', 'Ilorin West'),
    ('Kwara', 'Ilorin South'),
    ('Kwara', 'Ilorin East'),
    ('Lagos', 'Ikeja'),
    ('Lagos', 'Lagos Mainland'),
    ('Lagos', 'Lagos Island'),
    ('Nasarawa', 'Lafia'),
    ('Nasarawa', 'Nasarawa'),
    ('Nasarawa', 'Keffi'),
    ('Niger', 'Minna'),
    ('Niger', 'Suleja'),
    ('Niger', 'Bida'),
    ('Ogun', 'Abeokuta North'),
    ('Ogun', 'Abeokuta South'),
    ('Ogun', 'Ijebu North'),
    ('Ondo', 'Akure South'),
    ('Ondo', 'Akure North'),
    ('Ondo', 'Owo'),
    ('Osun', 'Osogbo'),
    ('Osun', 'Ife Central'),
    ('Osun', 'Ilesa East'),
    ('Oyo', 'Ibadan North'),
    ('Oyo', 'Ibadan South-East'),
    ('Oyo', 'Ibadan North-West'),
    ('Plateau', 'Jos North'),
    ('Plateau', 'Jos South'),
    ('Plateau', 'Barkin Ladi'),
    ('Rivers', 'Port Harcourt'),
    ('Rivers', 'Obio-Akpor'),
    ('Rivers', 'Ikwerre'),
    ('Sokoto', 'Sokoto North'),
    ('Sokoto', 'Sokoto South'),
    ('Sokoto', 'Wurno'),
    ('Taraba', 'Jalingo'),
    ('Taraba', 'Wukari'),
    ('Taraba', 'Takum'),
    ('Yobe', 'Damaturu'),
    ('Yobe', 'Potiskum'),
    ('Yobe', 'Gashua'),
    ('Zamfara', 'Gusau'),
    ('Zamfara', 'Kaura Namoda'),
    ('Zamfara', 'Talata Mafara'),
]

sample_hospitals = []
for idx, (st, lga_name) in enumerate(state_lga_pairs, start=1):
    for j in range(1, 4):
        sample_hospitals.append({
            'name': f'{lga_name} Hospital {j}',
            'country': 'Nigeria',
            'state': st,
            'lga': lga_name,
            'address': f'{j} {lga_name} Road, {lga_name}',
            'specialties': 'General Practice, Pediatrics',
            'services': 'Consultation, Vaccination, Maternity',
            'capabilities': 'Laboratory, Pharmacy, Emergency',
            'phone': f'+234800000{idx:03d}{j}',
            'email': f'{lga_name.lower().replace(" ", "")}{j}@caremesh.demo',
            'latitude': 0.0 + idx * 0.1 + j * 0.01,
            'longitude': 0.0 + idx * 0.1 + j * 0.01,
        })



def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_names = {h.name for h in db.query(Hospital).all()}
        for item in sample_hospitals:
            if item['name'] not in existing_names:
                db.add(Hospital(**item))
        db.commit()
        print('Seeded sample hospitals.')
    finally:
        db.close()


if __name__ == '__main__':
    run()
