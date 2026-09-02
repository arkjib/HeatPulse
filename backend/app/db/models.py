from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from app.db.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WardDemographic(Base):
    """
    Store for ward-level demographic data, which can eventually 
    replace the JSON file ingestion.
    """
    __tablename__ = "ward_demographics"

    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(String, unique=True, index=True) # e.g. W-01
    ward_name = Column(String)
    population = Column(Integer)
    pop_density_per_ha = Column(Float)
    elderly_share_pct = Column(Float)
    outdoor_worker_share_pct = Column(Float)
    healthcare_access_index = Column(Float)
    geojson_boundary = Column(JSON, nullable=True) # Store PostGIS/GeoJSON geometry

class AlertHistory(Base):
    """
    Log of all generated heatwave alerts and SMS dispatches.
    """
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ward_id = Column(String, index=True)
    alert_level = Column(String) # e.g., EXTREME_CAUTION
    message_content = Column(String)
    sms_dispatched = Column(Boolean, default=False)
    delivery_status = Column(String, nullable=True)
