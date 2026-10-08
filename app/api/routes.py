from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from app.schemas.schema import Item, Container, PlacedItem
from app.services.packer import BinPacker3D
from app.services.solver import WeightAndBalanceEngine
from app.database.database import get_db
from app.database.models import DBContainer

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
    return db.query(DBAircraft).all()


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