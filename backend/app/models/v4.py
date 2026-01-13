from __future__ import annotations

import uuid
import os

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.extensions import db

SRID = int(os.getenv("SRID", "4674"))

class Network(db.Model):
    __tablename__ = "networks"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = db.Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    name = db.Column(Text, nullable=False)
    description = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = db.relationship("User", backref="networks")


class V4Station(db.Model):
    """
    Core station entity for V4. 
    Replaces older station models.
    """
    __tablename__ = "stations_v4"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id = db.Column(UUID(as_uuid=True), ForeignKey("core.networks.id"), nullable=False)
    
    # Basic Info
    service = db.Column(Text, nullable=False) # FM, TV, etc
    status = db.Column(Text, nullable=False, default="P") # P=Proposta, L=Licenciada, etc.
    
    # Frequency / Channel
    canal = db.Column(Integer, nullable=True)
    freq_mhz = db.Column(Float, nullable=True) # Numeric might be better, but Float is standard in this app for now
    
    # Location
    uf = db.Column(Text, nullable=True)
    municipio = db.Column(Text, nullable=True)
    geom = db.Column(Geometry("POINT", srid=SRID, spatial_index=True), nullable=False)
    
    # Tech Params
    h_eff = db.Column(Float, nullable=True) # Heff max or avg? P.1546 usually requires heff per azimuth. This might be a reference value.
    htx = db.Column(Float, nullable=True) # Height of antenna center above ground (m)
    d_max = db.Column(Float, nullable=True) # Max calculation distance (km)
    
    # Metadata
    mosaico_id = db.Column(Text, nullable=True)
    entidade = db.Column(Text, nullable=True)
    erp_dbm = db.Column(Float, nullable=True)
    
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    network = db.relationship("Network", backref="stations")


class V4Antenna(db.Model):
    __tablename__ = "antennas_v4"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(Text, nullable=True)
    manufacturer = db.Column(Text, nullable=True)
    
    gain_dbd = db.Column(Float, nullable=False)
    tilt_el = db.Column(Float, nullable=False, default=0.0)
    
    # Patterns (0-360 deg -> atten/gain)
    pattern_h = db.Column(JSONB, nullable=False, default=dict)
    pattern_v = db.Column(JSONB, nullable=False, default=dict)
    
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Raster(db.Model):
    """
    Metadata for DEM files (HGT/GeoTIFF).
    """
    __tablename__ = "rasters"
    __table_args__ = {"schema": "gis"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = db.Column(Text, nullable=False, unique=True)
    bbox = db.Column(Geometry("POLYGON", srid=SRID, spatial_index=True), nullable=False)
    resolution_arcsec = db.Column(Float, nullable=False) # e.g. 1.0 or 3.0
    
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())


class Job(db.Model):
    """
    Async job tracking.
    """
    __tablename__ = "jobs"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id = db.Column(UUID(as_uuid=True), ForeignKey("core.networks.id"), nullable=True)
    
    type = db.Column(Text, nullable=False) # contour, interference, etc.
    status = db.Column(Text, nullable=False, default="queued") # queued, running, done, error
    progress = db.Column(Integer, nullable=False, default=0)
    
    params = db.Column(JSONB, nullable=True)
    result_ref = db.Column(JSONB, nullable=True) # e.g. {"contour_id": "..."}
    error = db.Column(Text, nullable=True)
    
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    network = db.relationship("Network", backref="jobs")


class Contour(db.Model):
    """
    Geospatial contours (isolinhas).
    """
    __tablename__ = "contours"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id = db.Column(UUID(as_uuid=True), ForeignKey("core.networks.id"), nullable=False)
    station_id = db.Column(UUID(as_uuid=True), ForeignKey("core.stations_v4.id"), nullable=True)
    
    field_strength_dbuvm = db.Column(Numeric, nullable=False)
    model = db.Column(Text, nullable=True) # e.g. "ITU1546_50_50"
    
    geom = db.Column(Geometry("MULTIPOLYGON", srid=SRID, spatial_index=True), nullable=False)
    
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())

    network = db.relationship("Network", backref="contours")
    station = db.relationship("V4Station", backref="contours")
