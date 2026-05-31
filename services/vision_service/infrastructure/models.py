from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Integer, JSON, Text
from sqlalchemy.orm import relationship
from services.shared.database import Base, BaseMixin, SoftDeleteMixin, GUID
import datetime

class AnonymousEntity(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = 'anonymous_entities'

    entity_hash = Column(Text, unique=True, index=True, nullable=False)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    camera_id = Column(GUID, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    behavior_score = Column(Float, default=0.0, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)

    # Backward compatibility helper property
    @property
    def entity_id(self) -> str:
        return self.entity_hash
    @entity_id.setter
    def entity_id(self, value: str):
        self.entity_hash = value

    behavior_signatures = relationship('BehaviorSignature', back_populates='entity')

class BehaviorSignature(Base, BaseMixin):
    __tablename__ = 'behavior_signatures'

    entity_id = Column(GUID, ForeignKey('anonymous_entities.id', ondelete='CASCADE'), nullable=False)
    movement_pattern = Column(JSON, nullable=True)  # maps to JSONB in PostgreSQL
    zone_history = Column(JSON, nullable=True)      # maps to JSONB in PostgreSQL
    object_history = Column(JSON, nullable=True)    # maps to JSONB in PostgreSQL
    activity_pattern = Column(JSON, nullable=True)  # maps to JSONB in PostgreSQL
    duration_seconds = Column(Integer, default=0, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=False)

    entity = relationship('AnonymousEntity', back_populates='behavior_signatures')

class Detection(Base, BaseMixin):
    __tablename__ = 'detections'

    camera_id = Column(GUID, nullable=False)
    entity_id = Column(GUID, nullable=False)
    class_name = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    bounding_box = Column(JSON, nullable=True)      # maps to JSONB in PostgreSQL
    frame_timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class VisionJob(Base, BaseMixin):
    __tablename__ = 'vision_jobs'

    job_id = Column(String(100), unique=True, index=True, nullable=False)
    camera_name = Column(String(100), nullable=False)
    status = Column(String(50), default="running", nullable=False)
    run_mode = Column(String(50), default="realtime", nullable=False)

class EntityTrack(Base, BaseMixin):
    __tablename__ = 'entity_tracks'

    entity_id = Column(String(100), unique=True, index=True, nullable=False)
    coordinate_path = Column(JSON, nullable=False)
    current_speed = Column(Float, default=0.0, nullable=False)
    last_seen = Column(String(100), nullable=False)
