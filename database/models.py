from sqlalchemy import Column, String, Float, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from database.database import Base

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
    name = Column(String, unique=True,index=True)
    max_cargo_weight = Column(Float)

    compatible_coontainers = relationship(
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
    contour_height = Column(Float, default = 0.0)

    weight = Column(Float)


    cog_target_x = Column(Float)
    cog_target_y = Column(Float)
    cog_target_z = Column(Float)
    cog_tolerance_x = Column(Float, default = 15.0)
    cog_tolerance_y = Column(Float, default = 15.0)
    cog_tolerance_z = Column(Float, default = 20.0)
    
    compatible_aircrafts = relationship(
        "DBAircraft",
        secondary=aircraft_container_association,
        back_populates="compatible_containers"
    )