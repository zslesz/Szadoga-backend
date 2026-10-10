from pydantic import BaseModel, Field
from typing import List, Tuple, Optional

class Item(BaseModel):
    """Egy doboz paraméterei"""
    id: str
    width: float
    height: float
    depth: float
    weight: float
    can_rotate: bool = True

    @property
    def volume (self) -> float:
        """Egy doboz térfogata köbcentiben"""
        return self.width * self.height * self.depth

class Container(BaseModel):
    """Egy konténer paraméterei"""
    id : str
    name : str
    width : float
    height : float
    depth : float
    max_weight : float

    base_width : Optional[float]= None
    contour_height : float = 0.0
    """Center of Gravity"""
    cog_target_x : float
    cog_target_y : float
    cog_target_z : float
    cog_tolerance_x : float = 15
    cog_tolerance_y : float = 15
    cog_tolerance_z : float = 20

    @property
    def max_volume (self) -> float:
        """Kontener belso terfogata kobcentiben"""
        return self.width * self.height * self.depth


class PlacedItem(BaseModel):
    item : Item
    x : float
    y : float
    z : float

    """Rotáció"""
    w : float
    h : float
    d : float


    @property
    def center_of_mass (self) -> Tuple[float, float, float]:
        cx = self.x + (self.w / 2.0)
        cy = self.y + (self.h / 2.0)
        cz = self.z + (self.d / 2.0)
        return cx, cy, cz


class ContainerResponse(BaseModel):
    id: str  # vagy int
    name: str

    # Ezt a három sort adtuk hozzá:
    max_gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    volume: Optional[float] = None

    class Config:
        from_attributes = True



class AircraftResponse(BaseModel):
    id: str
    name: str
    max_cargo_weight: Optional[float] = None
    body_type: Optional[str] = None
    range_km: Optional[float] = None  # vagy ahogy nálad hívják

    # EZ A LÉNYEG: Itt mondjuk meg a FastAPI-nak, hogy küldje át a listát!
    compatible_containers: List[ContainerResponse] = []

    class Config:
        from_attributes = True