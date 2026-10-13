from sqlalchemy.orm import Session
from sqlalchemy import insert, delete
from app.database.database import SessionLocal, engine
from app.database.models import Base, DBAircraft, DBContainer, aircraft_container_association, FuelProfile


def init_test_data():
    # Biztosítjuk, hogy a táblák léteznek
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=== Adatbázis inicializálása teszt adatokkal ===")

    try:
        containers = [
            {
                "id": "ULD-AKE", "name": "Standard AKE (LD3) Contoured",
                "width": 156.0, "height": 163.0, "depth": 153.0, "max_gross_weight": 1588.0,
                "tare_weight": 82.0,"volume": 4.3,
                "base_width": 110.0, "contour_height": 45.0,
                "cog_target_x": 78.0, "cog_target_y": 81.5, "cog_target_z": 76.5
            },
            {
                "id": "ULD-ALF", "name": "Standard ALF (LD6) Double-Contoured",
                "width": 317.0, "height": 163.0, "depth": 153.0, "max_gross_weight": 3175.0,
                "tare_weight": 230.0, "volume": 9.1,
                "base_width": 220.0, "contour_height": 45.0,
                "cog_target_x": 158.5, "cog_target_y": 81.5, "cog_target_z": 76.5
            },
            {
                "id": "ULD-PMC", "name": "PMC Main Deck Pallet (Rectangular)",
                "width": 317.0, "height": 244.0, "depth": 243.0, "max_gross_weight": 6800.0,
                "tare_weight": 120.0, "volume": 23.0,
                "base_width": 317.0, "contour_height": 0.0,
                "cog_target_x": 158.5, "cog_target_y": 122.0, "cog_target_z": 121.5
            },
            {
                "id": "ULD-AKH", "name": "Standard AKH (LD3-45W) for A321",
                "width": 153.4, "height": 114.3, "depth": 156.2, "max_gross_weight": 1134.0,
                "tare_weight": 92.0, "volume": 3.7,
                "base_width": 153.4, "contour_height": 45.0,
                "cog_target_x": 76.7, "cog_target_y": 57.1, "cog_target_z": 78.1
            }
        ]

        for c_data in containers:
            existing = db.query(DBContainer).filter(DBContainer.id == c_data["id"]).first()
            if not existing:
                db.add(DBContainer(**c_data))
                print(f"[+] Konténer hozzáadva: {c_data['id']}")
        db.commit()

        aircrafts = [
            {"id": "B747-400F", "name": "Boeing 747-400F / 747-8F", "max_cargo_weight": 134000.0,
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
            # B747-400F (max 42 AKE, 30 PMC)
            {"aircraft_id": "B747-400F", "container_id": "ULD-AKE", "max_quantity": 42},
            {"aircraft_id": "B747-400F", "container_id": "ULD-PMC", "max_quantity": 30},
            # B777F (max 32 AKE, 27 PMC, ALF-ből fele annyi fér, mint AKE-ből)
            {"aircraft_id": "B777F", "container_id": "ULD-AKE", "max_quantity": 32},
            {"aircraft_id": "B777F", "container_id": "ULD-PMC", "max_quantity": 27},
            {"aircraft_id": "B777F", "container_id": "ULD-ALF", "max_quantity": 16},
            # A330-300P2F
            {"aircraft_id": "A330-300P2F", "container_id": "ULD-AKE", "max_quantity": 32},
            {"aircraft_id": "A330-300P2F", "container_id": "ULD-PMC", "max_quantity": 26},
            # A330-200F
            {"aircraft_id": "A330-200F", "container_id": "ULD-AKE", "max_quantity": 26},
            {"aircraft_id": "A330-200F", "container_id": "ULD-PMC", "max_quantity": 22},
            # Narrow bodies (A321) -> AKH-val kompatibilisek
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