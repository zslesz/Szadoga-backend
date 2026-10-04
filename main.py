# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from uld_packing_core.models import Item, Container, PlacedItem
from uld_packing_core.packer import BinPacker3D
from uld_packing_core.solver import WeightAndBalanceEngine
from database import models
from database.database import engine

app = FastAPI(
    title="ULD Packing Optimizer API",
    description="Szakdolgozati REST API a 3D Bin Packing algoritmushoz",
    version="1.0.0"
)

models.Base.metadata.create_all(bind=engine)


class OptimizeRequest(BaseModel):
    container: Container
    items: List[Item]


class OptimizeResponse(BaseModel):
    placed_items: List[PlacedItem]
    unpacked_items: List[Item]
    utilization_pct: float
    cog_metrics: dict
    is_cog_valid: bool


@app.post("/api/v1/optimize", response_model=OptimizeResponse)
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