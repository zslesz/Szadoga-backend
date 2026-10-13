from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session, joinedload


from app.schemas.schema import Item, Container, PlacedItem
from app.services.packer import BinPacker3D
from app.services.solver import WeightAndBalanceEngine
from app.database.database import get_db
from app.database.models import DBContainer, FuelProfile
from app.services.fuelCalculator import FuelCalculator


from ..database.models import DBContainer, DBAircraft, aircraft_container_association

# Itt definiáljuk a közös útvonal-előtagot
router = APIRouter(prefix="/api/v1")

# Tipp: Ezeket a Pydantic modelleket később áthelyezheted az app/schemas/schema.py fájlba is
class OptimizeRequest(BaseModel):
    container: Container
    items: List[Item]

class OptimizeResponse(BaseModel):
    placed_items: List[PlacedItem]
    unpacked_items: List[Item]
    utilization_pct: float
    cog_metrics: dict
    is_cog_valid: bool

class FuelRequest(BaseModel):
    aircraft_id: str
    distance_km: float
    payload_kg: float

@router.post("/optimize", response_model=OptimizeResponse)
def optimize_packing(request: OptimizeRequest):
    """Bekér egy konténert és egy listányi dobozt, majd visszadja az optimalizált pakolási tervet."""
    packer = BinPacker3D(request.container)
    placed, unpacked = packer.pack(request.items)

    # Súlypont ellenőrzés
    valid, cog_metrics = WeightAndBalanceEngine.is_cog_valid(request.container, placed)

    # Térfogat-kihasználtság
    total_packed_volume = sum(p.item.volume for p in placed)
    utilization_pct = 0.0
    if request.container.max_volume > 0:
        utilization_pct = round((total_packed_volume / request.container.max_volume) * 100, 2)

    return OptimizeResponse(
        placed_items=placed,
        unpacked_items=unpacked,
        utilization_pct=utilization_pct,
        cog_metrics=cog_metrics,
        is_cog_valid=valid
    )

@router.get("/containers", response_model=List[Container])
def get_all_containers(db: Session = Depends(get_db)):
    """Lekérdezi az összes elérhető konténert az adatbázisból."""
    return db.query(DBContainer).all()


@router.get("/aircrafts")
def get_all_aircrafts(db: Session = Depends(get_db)):
    """Lekérdezi az összes elérhető repülőgépet az adatbázisból."""
    return db.query(DBAircraft).options(joinedload(DBAircraft.compatible_containers)).all()



@router.get("/aircrafts/{aircraft_id}/containers")
def get_compatible_containers(aircraft_id: str, db: Session = Depends(get_db)):
    """Lekérdezi egy adott géphez tartozó kompatibilis konténereket és a maximális darabszámukat."""

    compatible_data = db.query(
        DBContainer.id,
        DBContainer.name,
        aircraft_container_association.c.max_quantity
    ).join(
        aircraft_container_association,
        DBContainer.id == aircraft_container_association.c.container_id
    ).filter(
        aircraft_container_association.c.aircraft_id == aircraft_id
    ).all()

    return [
        {
            "container_id": row.id,
            "name": row.name,
            "max_quantity": row.max_quantity
        }
        for row in compatible_data
    ]


@router.post("/fuel/calculate")
def calculate_flight_fuel(request: FuelRequest, db: Session = Depends(get_db)):
    # 1. Kikeressük az adatbázisból az adott gép fogyasztási adatait
    profile = db.query(FuelProfile).filter(FuelProfile.aircraft_id == request.aircraft_id).first()

    if not profile:
        # Ha még nincs az adatbázisban, adunk egy biztonsági alapértelmezett értéket
        class DefaultProfile:
            speed_kmh = 850
            base_burn_kgh = 4000
            penalty_per_tonne = 20
            reserve_fuel_kg = 3000

        profile = DefaultProfile()

    # 2. Lefuttatjuk a fuel_calculator.py-t
    result = FuelCalculator.calculate(
        distance_km=request.distance_km,
        payload_kg=request.payload_kg,
        profile=profile
    )

    # 3. Visszaküldjük a Reactnek a kész adatokat
    return result