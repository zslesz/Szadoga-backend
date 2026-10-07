from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import models
from app.database.database import engine
from scripts.init_db import init_test_data

# Beimportáljuk az útvonalakat az új fájlból
from app.api.routes import router as api_router

# Élettartam-kezelő (lifespan) az automatikus lefutáshoz
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Szerver indulása: Adatbázis inicializálás ellenőrzése...")
    init_test_data()
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

# Adatbázis táblák létrehozása (ha még nem léteznének)
models.Base.metadata.create_all(bind=engine)

# Végpontok (router) becsatlakoztatása az alkalmazásba
app.include_router(api_router)