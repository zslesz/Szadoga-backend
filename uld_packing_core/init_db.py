# init_db.py
from database.database import SessionLocal, engine
from database.models import Base, DBAircraft, DBContainer


def init_test_data():
    # Biztosítjuk, hogy a táblák léteznek
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=== Adatbázis inicializálása teszt adatokkal ===")

    # 1. Repülőgépek (Aircrafts)
    aircrafts = [
        {"id": "B777F", "name": "Boeing 777 Freighter", "max_cargo_weight": 102000.0},
        {"id": "A330F", "name": "Airbus A330-200F", "max_cargo_weight": 70000.0}
    ]

    for ac_data in aircrafts:
        existing = db.query(DBAircraft).filter(DBAircraft.id == ac_data["id"]).first()
        if not existing:
            db.add(DBAircraft(**ac_data))
            print(f"[+] Repülőgép hozzáadva: {ac_data['id']}")

    db.commit()

    # 2. Konténerek (Containers) ferde kontúr adatokkal
    containers = [
        {
            "id": "ULD-AKE", "name": "Standard AKE (LD3) Contoured",
            "width": 156.0, "height": 163.0, "depth": 153.0, "max_weight": 1588.0,
            "base_width": 110.0, "contour_height": 45.0,
            "cog_target_x": 78.0, "cog_target_y": 81.5, "cog_target_z": 76.5
        },
        {
            "id": "ULD-ALF", "name": "Standard ALF (LD6) Double-Contoured",
            "width": 317.0, "height": 163.0, "depth": 153.0, "max_weight": 3175.0,
            "base_width": 220.0, "contour_height": 45.0,
            "cog_target_x": 158.5, "cog_target_y": 81.5, "cog_target_z": 76.5
        },
        {
            "id": "ULD-PMC", "name": "PMC Main Deck Pallet (Rectangular)",
            "width": 317.0, "height": 244.0, "depth": 243.0, "max_weight": 6800.0,
            "base_width": 317.0, "contour_height": 0.0,  # Szögletes, nincs kontúr
            "cog_target_x": 158.5, "cog_target_y": 122.0, "cog_target_z": 121.5
        }
    ]

    for c_data in containers:
        existing = db.query(DBContainer).filter(DBContainer.id == c_data["id"]).first()
        if not existing:
            db.add(DBContainer(**c_data))
            print(f"[+] Konténer hozzáadva: {c_data['id']}")

    db.commit()

    # 3. Kapcsolatok (Many-to-Many) beállítása
    b777f = db.query(DBAircraft).filter(DBAircraft.id == "B777F").first()
    a330f = db.query(DBAircraft).filter(DBAircraft.id == "A330F").first()

    ake = db.query(DBContainer).filter(DBContainer.id == "ULD-AKE").first()
    alf = db.query(DBContainer).filter(DBContainer.id == "ULD-ALF").first()
    pmc = db.query(DBContainer).filter(DBContainer.id == "ULD-PMC").first()

    if b777f:
        for c in [ake, alf, pmc]:
            if c and c not in b777f.compatible_containers:
                b777f.compatible_containers.append(c)
        print("[+] B777F kompatibilitási kapcsolatok beállítva.")

    if a330f:
        for c in [ake, alf]:  # Az Airbus A330F-hez most csak az alsó fedélzeti ULD-ket kötjük
            if c and c not in a330f.compatible_containers:
                a330f.compatible_containers.append(c)
        print("[+] A330F kompatibilitási kapcsolatok beállítva.")

    db.commit()
    db.close()
    print("=== Inicializálás sikeresen befejeződött! ===")


if __name__ == "__main__":
    init_test_data()