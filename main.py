from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import models
from app.database.database import engine
from scripts.init_db import init_test_data

# Beimportáljuk az útvonalakat az új fájlból
from app.api.routes import router as api_router

# Élettartam-kezelő (lifespan) az automatikus lefutáshoz
import time
from sqlalchemy.exc import OperationalError


# (A többi importod marad, ami eddig is ott volt)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Szerver indulása: Adatbázis inicializálás ellenőrzése...")

    # 1. Várakozás az adatbázisra (Retry mechanizmus)
    retries = 5
    while retries > 0:
        try:
            # Ide mozgattuk be a táblák létrehozását!
            models.Base.metadata.create_all(bind=engine)
            print("✔ Adatbázis elérhető, táblák sikeresen ellenőrizve.")
            break
        except OperationalError:
            print(f"⏳ Adatbázis még éledezik... várakozás 2 másodpercet (Hátralévő kísérlet: {retries - 1})")
            time.sleep(2)
            retries -= 1

    # 2. Adatok feltöltése a repülőkkel és ULD-kkel
    try:
        init_test_data()
    except Exception as e:
        print(f"❌ Hiba az adatok feltöltésekor: {e}")

    yield
    print("Szerver leállítása...")

app = FastAPI(
    title="ULD Packing Optimizer API",
    description="Szakdolgozati REST API a 3D Bin Packing algoritmushoz",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Végpontok (router) becsatlakoztatása az alkalmazásba
app.include_router(api_router)