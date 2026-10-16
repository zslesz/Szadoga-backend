from sqlalchemy.orm import Session
from sqlalchemy import insert, delete
from passlib.context import CryptContext
from app.database.database import SessionLocal, engine
from app.database.models import Base, DBAircraft, DBContainer, aircraft_container_association, FuelProfile, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated=['auto'])

def get_password_hash(password):
    return pwd_context.hash(password)


def init_test_data():
    # Biztosítjuk, hogy a táblák léteznek
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=== Adatbázis inicializálása teszt adatokkal ===")

    try:
        containers = [
            {
                "id": "ULD-PMC", "name": "PMC Main Deck Pallet (Rectangular)",
                "width": 317.5, "height": 243.8, "depth": 243.8, "max_gross_weight": 6804.0,
                "tare_weight": 93.9, "volume": 18.8,
                "base_width": 317.5, "contour_height": 0.0,
                "cog_target_x": 158.75, "cog_target_y": 121.9, "cog_target_z": 121.9
            },
            {
                "id": "ULD-AKE", "name": "Standard AKE (LD3) Contoured",
                "width": 199.3, "height": 161.3, "depth": 153.4, "max_gross_weight": 1588.0,
                "tare_weight": 54.0,"volume": 4.3,
                "base_width": 156.1, "contour_height": 45.0,
                "cog_target_x": 99.65, "cog_target_y": 80.65, "cog_target_z": 76.7
            },
            {
                "id": "ULD-DQF", "name": "Standard DQF (LD8) Double-Contoured",
                "width": 317.5, "height": 162.6, "depth": 153.4, "max_gross_weight": 2450.0,
                "tare_weight": 127.0, "volume": 7.2,
                "base_width": 243.8, "contour_height": 45.0,
                "cog_target_x": 158.75, "cog_target_y": 81.3, "cog_target_z": 76.7
            },

            {
                "id": "ULD-DPE", "name": "Standard DPE (LD2) Contoured",
                "width": 156.2, "height": 162.6, "depth": 153.4, "max_gross_weight": 1225.0,
                "tare_weight": 73.0, "volume": 3.5,
                "base_width": 119.4, "contour_height": 45.0,
                "cog_target_x": 78.1, "cog_target_y": 81.3, "cog_target_z": 76.7
            },
            {
                "id": "ULD-AKH", "name": "Standard AKH (LD3-45W) Double-Contoured",
                "width": 243.8, "height": 114.3, "depth": 156.2, "max_gross_weight": 1134.0,
                "tare_weight": 88.0, "volume": 3.7,
                "base_width": 153.4, "contour_height": 45.0,
                "cog_target_x": 121.9, "cog_target_y": 57.15, "cog_target_z": 78.1
            }
        ]

        for c_data in containers:
            existing = db.query(DBContainer).filter(DBContainer.id == c_data["id"]).first()
            if not existing:
                db.add(DBContainer(**c_data))
                print(f"[+] Konténer hozzáadva: {c_data['id']}")
        db.commit()

        aircrafts = [
            {"id": "B747-400F", "name": "Boeing 747-400F", "max_cargo_weight": 134000.0,
             "body_type": "wide-body", "max_range_km": 8334.0},
            {"id": "B777F", "name": "Boeing 777F", "max_cargo_weight": 102000.0, "body_type": "wide-body",
             "max_range_km": 9075.0},
            {"id": "A330-300P2F", "name": "Airbus A330-300P2F", "max_cargo_weight": 60000.0, "body_type": "wide-body",
             "max_range_km": 6850.0},
            {"id": "B767-300F", "name": "Boeing 767-300F", "max_cargo_weight": 52000.0, "body_type": "wide-body",
             "max_range_km": 5930.0},
            {"id": "A300-600F", "name": "Airbus A300-600F", "max_cargo_weight": 48000.0, "body_type": "wide-body",
             "max_range_km": 4630.0},
            {"id": "A330-200F", "name": "Airbus A330-200F", "max_cargo_weight": 65000.0, "body_type": "wide-body",
             "max_range_km": 5930.0},
            {"id": "A321XLR", "name": "Airbus A321XLR", "max_cargo_weight": 25500.0, "body_type": "narrow-body",
             "max_range_km": 8700.0},
            {"id": "A321NEO", "name": "Airbus A321 Neo", "max_cargo_weight": 25000.0, "body_type": "narrow-body",
             "max_range_km": 7400.0},
        ]

        for ac_data in aircrafts:
            existing = db.query(DBAircraft).filter(DBAircraft.id == ac_data["id"]).first()
            if not existing:
                db.add(DBAircraft(**ac_data))
                print(f"[+] Repülőgép hozzáadva: {ac_data['id']}")
        db.commit()

        print("[*] Kompatibilitási mátrix építése...")
        db.execute(delete(aircraft_container_association))  # Töröljük a régit, hogy ne duplikáljunk

        associations = [
            {"aircraft_id": "B747-400F", "container_id": "ULD-AKE", "max_quantity": 42},
            {"aircraft_id": "B747-400F", "container_id": "ULD-PMC", "max_quantity": 39},

            {"aircraft_id": "B777F", "container_id": "ULD-AKE", "max_quantity": 32},
            {"aircraft_id": "B777F", "container_id": "ULD-PMC", "max_quantity": 27},

            {"aircraft_id": "A330-300P2F", "container_id": "ULD-AKE", "max_quantity": 32},
            {"aircraft_id": "A330-300P2F", "container_id": "ULD-PMC", "max_quantity": 26},

            {"aircraft_id": "B767-300F", "container_id": "ULD-PMC", "max_quantity": 24},
            {"aircraft_id": "B767-300F", "container_id": "ULD-DQF", "max_quantity": 15},
            {"aircraft_id": "B767-300F", "container_id": "ULD-DPE", "max_quantity": 30},

            {"aircraft_id": "A300-600F", "container_id": "ULD-AKE", "max_quantity": 22},
            {"aircraft_id": "A300-600F", "container_id": "ULD-PMC", "max_quantity": 15},

            {"aircraft_id": "A330-200F", "container_id": "ULD-AKE", "max_quantity": 26},
            {"aircraft_id": "A330-200F", "container_id": "ULD-PMC", "max_quantity": 22},


            {"aircraft_id": "A321XLR", "container_id": "ULD-AKH", "max_quantity": 10},

            {"aircraft_id": "A321NEO", "container_id": "ULD-AKH", "max_quantity": 10},
        ]

        db.execute(insert(aircraft_container_association).values(associations))
        db.commit()


        # 4. Üzemanyag profilok (Fuel Profiles) felvétele
        print("[*] Üzemanyag-fogyasztási profilok (Fuel Profiles) betöltése...")
        fuel_profiles = [
            {"aircraft_id": "B747-400F", "speed_kmh": 910, "base_burn_kgh": 8000, "penalty_per_tonne": 35, "reserve_fuel_kg": 7000},
            {"aircraft_id": "B777F", "speed_kmh": 900, "base_burn_kgh": 5500, "penalty_per_tonne": 30, "reserve_fuel_kg": 5400},
            {"aircraft_id": "A330-300P2F", "speed_kmh": 870, "base_burn_kgh": 4800, "penalty_per_tonne": 25, "reserve_fuel_kg": 4500},
            {"aircraft_id": "B767-300F", "speed_kmh": 850, "base_burn_kgh": 4000, "penalty_per_tonne": 20, "reserve_fuel_kg": 3500},
            {"aircraft_id": "A300-600F", "speed_kmh": 840, "base_burn_kgh": 4200, "penalty_per_tonne": 22, "reserve_fuel_kg": 3800},
            {"aircraft_id": "A330-200F", "speed_kmh": 870, "base_burn_kgh": 4600, "penalty_per_tonne": 24, "reserve_fuel_kg": 4500},
            {"aircraft_id": "A321XLR", "speed_kmh": 830, "base_burn_kgh": 2200, "penalty_per_tonne": 12, "reserve_fuel_kg": 2000},
            {"aircraft_id": "A321NEO", "speed_kmh": 830, "base_burn_kgh": 2100, "penalty_per_tonne": 12, "reserve_fuel_kg": 1800},
        ]

        for fp_data in fuel_profiles:
            existing = db.query(FuelProfile).filter(FuelProfile.aircraft_id == fp_data["aircraft_id"]).first()
            if not existing:
                db.add(FuelProfile(**fp_data))
                print(f"[+] FuelProfile hozzáadva: {fp_data['aircraft_id']}")
            else:
                # Opcionális: Ha frissíteni szeretnéd a már meglévő adatokat az új értékekre
                for key, value in fp_data.items():
                    setattr(existing, key, value)
                print(f"[*] FuelProfile frissítve: {fp_data['aircraft_id']}")
        db.commit()

        print("=== Inicializálás sikeresen befejeződött! ===")

    except Exception as e:
        print(f"❌ Hiba az adatbázis inicializálásakor: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()