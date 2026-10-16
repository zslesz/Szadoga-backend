from app.database.database import SessionLocal, engine
from app.database.models import Base, Fleet

# Ha kell, újra létrehozzuk a táblákat
Base.metadata.create_all(bind=engine)


def seed_fleet():
    db = SessionLocal()
    try:
        # Ha már van adat, nem teszünk be újat
        if db.query(Fleet).first():
            print("A flotta már fel van töltve.")
            return

        test_fleet = [
            # Boeing 747-400F (1 db)
            Fleet(registration="HA-LQA", status="Available", aircraft_type_id="B747-400F"),

            # Boeing 777F (2 db)
            Fleet(registration="HA-LQB", status="Available", aircraft_type_id="B777F"),
            Fleet(registration="HA-LQC", status="Available", aircraft_type_id="B777F"),

            # Airbus A330-300P2F (1 db)
            Fleet(registration="HA-LQD", status="Available", aircraft_type_id="A330-300P2F"),

            # Boeing 767-300F (2 db)
            Fleet(registration="HA-LQE", status="Available", aircraft_type_id="B767-300F"),
            Fleet(registration="HA-LQF", status="Available", aircraft_type_id="B767-300F"),

            # Airbus A300-600F (1 db)
            Fleet(registration="HA-LQG", status="Available", aircraft_type_id="A300-600F"),

            # Airbus A330-200F (2 db)
            Fleet(registration="HA-LQH", status="Available", aircraft_type_id="A330-200F"),
            Fleet(registration="HA-LQI", status="Available", aircraft_type_id="A330-200F"),

            # Airbus A321XLR (1 db)
            Fleet(registration="HA-LQJ", status="Available", aircraft_type_id="A321XLR"),

            # Airbus A321 Neo (1 db)
            Fleet(registration="HA-LQK", status="Available", aircraft_type_id="A321NEO"),
        ]

        db.add_all(test_fleet)
        db.commit()
        print(f"Sikeresen hozzáadva {len(test_fleet)} repülőgép mind a 8 típusból a flottához!")
    except Exception as e:
        print(f"Hiba: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_fleet()