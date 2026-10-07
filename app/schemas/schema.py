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