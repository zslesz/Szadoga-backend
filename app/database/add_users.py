from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine
from app.database.models import Base, User
from passlib.context import CryptContext

# Biztosítjuk a táblákat
Base.metadata.create_all(bind=engine)

# Jelszó titkosító beállítása
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def seed_users():
    db = SessionLocal()
    print("=== Felhasználók feltöltése ===")

    test_users = [
        {
            "username": "Admin",
            "hashed_password": get_password_hash("admin"),
            "role": "admin"
        },
        {
            "username": "Cargo Agent",
            "hashed_password": get_password_hash("cargoagent"),
            "role": "cargo agent"
        },
        {
            "username": "Loadmaster",
            "hashed_password": get_password_hash("loadmaster"),
            "role": "loadmaster"
        }
    ]

    added_count = 0

    for user_data in test_users:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            new_user = User(
                username=user_data["username"],
                hashed_password=user_data["hashed_password"],
                role=user_data["role"]
            )
            db.add(new_user)
            added_count += 1
            print(f"[+] Hozzáadva: {user_data['username']} ({user_data['role']})")
        else:
            print(f"[*] Már létezik: {user_data['username']}")

    # Mentés az adatbázisba
    db.commit()
    db.close()

    print(f"=== Kész! {added_count} új felhasználó bekerült az adatbázisba. ===")


if __name__ == "__main__":
    seed_users()