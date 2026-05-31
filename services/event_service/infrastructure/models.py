from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from services.shared.database import Base, TenantMixin

class ThreatEvent(Base, TenantMixin):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=True)
    event_type = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    entity_id = Column(String(100), index=True, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="unresolved", nullable=False)
    reasoning = Column(String(1000), nullable=True)
    is_false_positive = Column(Boolean, default=False, nullable=False)

class ThreatEvidence(Base, TenantMixin):
    __tablename__ = 'event_evidence'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey('events.event_id', ondelete='CASCADE'), nullable=True)
    image_snapshot_url = Column(String(255), nullable=False)
    video_clip_url = Column(String(255), nullable=True)
    encryption_meta = Column(JSON, nullable=True)

class ThreatTimeline(Base, TenantMixin):
    __tablename__ = 'event_timelines'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey('events.event_id', ondelete='CASCADE'), nullable=True)
    events_sequence = Column(JSON, nullable=False)
