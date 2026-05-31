from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from services.shared.database import Base, TenantMixin

class AnonymousEntity(Base, TenantMixin):
    __tablename__ = 'anonymous_entities'
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String(100), unique=True, index=True, nullable=False)
    last_location = Column(String(255), nullable=False)
    risk_score = Column(Float, default=0.0)
    behavior_signature = Column(String(255), nullable=True)
    movement_profile = Column(String(255), nullable=True)
    zone_profile = Column(String(255), nullable=True)
    object_profile = Column(String(255), nullable=True)
    duration_profile = Column(String(255), nullable=True)
    status = Column(String(50), default="active", nullable=False)

class VisionJob(Base, TenantMixin):
    __tablename__ = 'vision_jobs'

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    camera_name = Column(String(100), nullable=False)
    status = Column(String(50), default="running", nullable=False)
    run_mode = Column(String(50), default="realtime", nullable=False)

class Detection(Base, TenantMixin):
    __tablename__ = 'detections'

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(String(100), unique=True, index=True, nullable=False)
    entity_id = Column(String(100), index=True, nullable=False)
    location = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    object_class = Column(String(100), nullable=False)
    timestamp = Column(String(100), nullable=False)

class EntityTrack(Base, TenantMixin):
    __tablename__ = 'entity_tracks'

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String(100), unique=True, index=True, nullable=False)
    coordinate_path = Column(JSON, nullable=False)  # Stores coordinate arrays: [{"x": 100, "y": 200, "time": ...}]
    current_speed = Column(Float, default=0.0, nullable=False)
    last_seen = Column(String(100), nullable=False)
