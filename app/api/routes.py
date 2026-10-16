from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Any
from sqlalchemy.orm import Session, joinedload
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import json



from app.schemas.schema import Item, Container, PlacedItem
from app.services.packer import BinPacker3D
from app.services.solver import WeightAndBalanceEngine
from app.database.database import get_db
from app.database.models import DBContainer, FuelProfile, User, CargoOrder, Fleet, DBAircraft, aircraft_container_association
from app.services.fuelCalculator import FuelCalculator
from app.services.auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES


class OrderCreateSchema(BaseModel):
    customer_name: str
    distance_km: float
    items: List[Any]



# Itt definiáljuk a közös útvonal-előtagot
router = APIRouter(prefix="/api/v1")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Felhasználó keresése az adatbázisban
    user = db.query(User).filter(User.username == form_data.username).first()

    # 2. Jelszó ellenőrzése
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Hibás felhasználónév vagy jelszó!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Token generálása (figyelve, hogy az oszlop neve 'roles' az adatbázisban)
    user_role = getattr(user, 'roles', getattr(user, 'role', 'viewer'))
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user_role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "role": user_role}

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

class OrderApproveSchema(BaseModel):
    aircraft_type_id: str

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


@router.post("/orders")
def create_order(order: OrderCreateSchema, db: Session = Depends(get_db)):
    # Létrehozzuk a rendelést, de NEM rendelünk hozzá gépet (az a Cargo Agent feladata lesz)
    new_order = CargoOrder(
        customer_name=order.customer_name,
        distance_km=order.distance_km,
        items_json=json.dumps(order.items),
        status="pending"
        # A fleet_id alapértelmezetten NULL (üres) marad
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Rendelés sikeresen mentve! A Cargo Agent hamarosan feldolgozza.",
        "order_id": new_order.id
    }


# --- 2. VÉGPONT: CARGO AGENT LEKÉRI A FÜGGŐBEN LÉVŐKET ---
@router.get("/orders")
def get_pending_orders(db: Session = Depends(get_db)):
    orders = db.query(CargoOrder).filter(CargoOrder.status == "pending").all()

    result = []
    for o in orders:
        items_list = json.loads(o.items_json)
        # Kiszámoljuk az összsúlyt, hogy az Agent már a panelen lássa, mekkora gépre lesz szükség
        total_weight = sum(item.get("weight", 0) for item in items_list)

        result.append({
            "id": o.id,
            "customer_name": o.customer_name,
            "distance_km": o.distance_km,
            "items": items_list,
            "total_weight": total_weight,
            "status": o.status
        })
    return result


class OrderApproveSchema(BaseModel):
    aircraft_type_id: str

@router.post("/orders/{order_id}/approve")
def approve_order(order_id: int, payload: OrderApproveSchema, db: Session = Depends(get_db)):
    # 1. Megkeressük a rendelést
    order = db.query(CargoOrder).filter(CargoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Rendelés nem található")

    # 2. Keresünk a flottában egy SZABAD gépet abból a TÍPUSBÓL, amit az Agent kiválasztott
    available_fleet = db.query(Fleet).filter(
        Fleet.aircraft_type_id == payload.aircraft_type_id,
        Fleet.status == "Available"
    ).first()

    if not available_fleet:
        raise HTTPException(status_code=400, detail="Nincs szabad gép ebből a típusból a flottában!")

    # 3. Frissítjük a státuszokat (ERP logika!)
    order.status = "packed"                  # A rendelés teljesítve
    order.fleet_id = available_fleet.id      # Összekötjük a konkrét géppel
    available_fleet.status = "In Transit"    # A gép felszállt, foglalt lett

    db.commit()

    return {
        "message": f"Sikeres jóváhagyás! A {available_fleet.registration} lajstromjelű gép útnak indult."
    }

@router.post("/orders/{order_id}/approve")
def approve_order(order_id: int, payload: OrderApproveSchema, db: Session = Depends(get_db)):
    order = db.query(CargoOrder).filter(CargoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Rendelés nem található")

    available_fleet = db.query(Fleet).filter(
        Fleet.aircraft_type_id == payload.aircraft_type_id,
        Fleet.status == "Available"
    ).first()

    if not available_fleet:
        raise HTTPException(status_code=400, detail="Nincs szabad gép ebből a típusból a flottában!")

    order.status = "packed"
    order.fleet_id = available_fleet.id
    available_fleet.status = "In Transit"

    db.commit()

    return {"message": f"Sikeres jóváhagyás! A {available_fleet.registration} lajstromjelű gép útnak indult."}


@router.post("/fleet/{fleet_id}/arrive")
def arrive_aircraft(fleet_id: int, db: Session = Depends(get_db)):
    # Megkeressük a gépet a flottában
    aircraft = db.query(Fleet).filter(Fleet.id == fleet_id).first()

    if not aircraft:
        raise HTTPException(status_code=404, detail="Gép nem található")

    if aircraft.status != "In Transit":
        raise HTTPException(status_code=400, detail="Ez a gép jelenleg nincs úton!")

    # Visszaállítjuk szabadra, hogy újra lehessen pakolni
    aircraft.status = "Available"
    db.commit()

    return {"message": f"A {aircraft.registration} lajstromjelű gép sikeresen megérkezett és újra elérhető!"}


@router.get("/fleet/intransit")
def get_in_transit_fleet(db: Session = Depends(get_db)):
    # Lekérjük az összes gépet, ami épp "Úton" (In Transit) van
    flying_planes = db.query(Fleet).filter(Fleet.status == "In Transit").all()

    result = []
    for plane in flying_planes:
        result.append({
            "id": plane.id,
            "registration": plane.registration,
            "aircraft_type_id": plane.aircraft_type_id,
            "status": plane.status
        })
    return result