from sqlalchemy import Column, String, Float, ForeignKey, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from services.shared.database import Base, BaseMixin, SoftDeleteMixin, GUID
import datetime

class Event(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = 'events'

    event_type = Column(String(100), nullable=False)  # THEFT, INTRUSION, WEAPON, FIRE, PANIC, VIOLENCE, MEDICAL
    camera_id = Column(GUID, nullable=True)
    entity_id = Column(GUID, nullable=True)
    risk_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    severity = Column(String(20), default="medium", nullable=False)
    status = Column(String(20), default="unresolved", nullable=False)

    # Compatibility attributes
    location = Column(String(255), nullable=True)
    reasoning = Column(String(1000), nullable=True)
    is_false_positive = Column(Boolean, default=False, nullable=True)

    # Backward compatibility properties
    @property
    def event_id(self) -> str:
        return str(self.id)

    timelines = relationship('EventTimeline', back_populates='event')
    evidence = relationship('EventEvidence', back_populates='event')
    explanations = relationship('EventExplanation', back_populates='event')

class EventTimeline(Base, BaseMixin):
    __tablename__ = 'event_timelines'

    event_id = Column(GUID, ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    timeline_data = Column(JSON, nullable=True)  # maps to JSONB in PostgreSQL

    event = relationship('Event', back_populates='timelines')

class EventEvidence(Base, BaseMixin):
    __tablename__ = 'event_evidence'

    event_id = Column(GUID, ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    evidence_type = Column(String(50), nullable=False)  # VIDEO, IMAGE, REPORT
    file_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)

    event = relationship('Event', back_populates='evidence')

class EventExplanation(Base, BaseMixin):
    __tablename__ = 'event_explanations'

    event_id = Column(GUID, ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    reason = Column(String(255), nullable=False)
    weight = Column(Float, default=0.0, nullable=False)
    description = Column(Text, nullable=True)

    event = relationship('Event', back_populates='explanations')
