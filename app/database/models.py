from sqlalchemy import Column, String, Float, ForeignKey, Table, Integer, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base

aircraft_container_association = Table(
    'aircraft_container_compatibility',
    Base.metadata,
    Column("aircraft_id", String, ForeignKey('aircrafts.id'), primary_key=True),
    Column("container_id", String, ForeignKey('containers.id'), primary_key=True),
    Column("max_quantity", Float, nullable=True),
)


class DBAircraft(Base):
    __tablename__ = 'aircrafts'

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    max_cargo_weight = Column(Float)

    # EZ A KÉT SOR HIÁNYZIK:
    body_type = Column(String, nullable=True)
    max_range_km = Column(Float, nullable=True)

    # Kapcsolat a konténerek felé (ez már megvan nálad)
    compatible_containers = relationship(
        "DBContainer",
        secondary=aircraft_container_association,
        back_populates="compatible_aircrafts"
    )


class DBContainer(Base):
    __tablename__ = 'containers'
    id = Column(String, primary_key=True, index=True)
    name = Column(String)

    width = Column(Float)
    height = Column(Float)
    depth = Column(Float)

    """A konténer contourja"""
    base_width = Column(Float, nullable=True)
    contour_height = Column(Float, default=0.0)

    max_gross_weight = Column(Float)
    tare_weight = Column(Float)
    volume = Column(Float)

    cog_target_x = Column(Float)
    cog_target_y = Column(Float)
    cog_target_z = Column(Float)
    cog_tolerance_x = Column(Float, default=15.0)
    cog_tolerance_y = Column(Float, default=15.0)
    cog_tolerance_z = Column(Float, default=20.0)

    compatible_aircrafts = relationship(
        "DBAircraft",
        secondary=aircraft_container_association,
        back_populates="compatible_containers"
    )

class FuelProfile(Base):
    __tablename__ = 'fuel_profiles'
    id = Column(Integer, primary_key=True, index=True)
    aircraft_id = Column(String, ForeignKey('aircrafts.id'), unique=True)

    speed_kmh = Column(Integer, default=900)
    base_burn_kgh = Column(Integer, default=5500)
    penalty_per_tonne = Column(Integer, default=30)
    reserve_fuel_kg = Column(Integer, default=5400)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="viewer")
    is_active = Column(Boolean, default=True)

