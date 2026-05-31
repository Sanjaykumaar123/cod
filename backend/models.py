import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin, auditor, officer, viewer
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    rtsp_url = Column(String, nullable=True)
    location = Column(String, nullable=False)
    status = Column(String, default="active")  # active, offline
    resolution = Column(String, default="1080p")
    fps = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    privacy_shield_active = Column(Boolean, default=True)
    safety_score = Column(Float, default=95.0)
    threat_count = Column(Integer, default=0)

class AnonymousEntity(Base):
    __tablename__ = "anonymous_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, unique=True, index=True, nullable=False) # e.g., Entity_93A7
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_location = Column(String, nullable=False)
    risk_score = Column(Float, default=0.0)
    
    # Behavior Signature details
    behavior_signature = Column(String, nullable=True) # Hash or summary of behavior
    movement_profile = Column(String, nullable=True)    # pace, paths
    zone_profile = Column(String, nullable=True)        # public vs restricted zones visited
    object_profile = Column(String, nullable=True)      # carried items, interactions
    duration_profile = Column(String, nullable=True)    # dwell times
    status = Column(String, default="active")           # active, departed

class EntityTrack(Base):
    __tablename__ = "entity_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, ForeignKey("anonymous_entities.entity_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    location_x = Column(Integer, nullable=False)
    location_y = Column(Integer, nullable=False)
    zone = Column(String, nullable=False)
    risk_score = Column(Float, default=0.0)
    speed = Column(Float, default=0.0)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False) # Possible Theft, Possible Violence, Possible Weapon, Possible Intrusion, Fire Hazard, Crowd Panic, Medical Emergency
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    location = Column(String, nullable=False)
    entity_id = Column(String, ForeignKey("anonymous_entities.entity_id"), nullable=True)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_image = Column(Text, nullable=True) # Base64 or local path
    reasoning = Column(Text, nullable=False) # Explainable AI reason
    timeline = Column(Text, nullable=True) # JSON string of event progression
    status = Column(String, default="unresolved") # unresolved, acknowledged, resolved, false_positive
    is_false_positive = Column(Boolean, default=False)

class IdentityRequest(Base):
    __tablename__ = "identity_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requester_name = Column(String, nullable=False)
    entity_id = Column(String, ForeignKey("anonymous_entities.entity_id"), nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(String, default="pending") # pending, approved, rejected, expired
    duration_minutes = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    approved_by_auditor = Column(Boolean, default=False)
    approved_by_admin = Column(Boolean, default=False)
    approved_by_auditor_name = Column(String, nullable=True)
    approved_by_admin_name = Column(String, nullable=True)
    approved_by_auditor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    expires_at = Column(DateTime, nullable=True)
    decrypted_identity = Column(String, nullable=True) # The identity that gets decrypted (mock name/SSN/etc)
    encrypted_identity = Column(String, nullable=True) # The ciphertext
    auditor_key_share = Column(String, nullable=True)  # Cryptographic share A
    admin_key_share = Column(String, nullable=True)    # Cryptographic share B

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # Can be null for system actions or unauthenticated
    username = Column(String, nullable=True)
    role = Column(String, nullable=True)
    action = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    outcome = Column(String, nullable=False) # success, denied, failed
    ip_address = Column(String, nullable=True)
    hash = Column(String, nullable=True)
    previous_hash = Column(String, nullable=True)

class PrivacyMetric(Base):
    __tablename__ = "privacy_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    privacy_score = Column(Float, default=100.0)
    compliance_score = Column(Float, default=100.0)
    transparency_score = Column(Float, default=100.0)
    retention_risk = Column(String, default="Low") # Low, Medium, High
    exposure_risk = Column(String, default="Low")  # Low, Medium, High
    active_anonymous_count = Column(Integer, default=0)
    requests_denied = Column(Integer, default=0)
    requests_approved = Column(Integer, default=0)

class SimulationResult(Base):
    __tablename__ = "simulation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    config_name = Column(String, nullable=False)
    cameras_count = Column(Integer, nullable=False)
    retention_days = Column(Integer, nullable=False)
    sensitivity = Column(Float, nullable=False)
    identity_collection = Column(String, nullable=False) # default_anonymized, stored_by_default
    crowd_density = Column(String, nullable=False) # low, medium, high
    threat_level = Column(String, nullable=False)  # low, medium, high
    
    # Calculated scores
    safety_score = Column(Float, nullable=False)
    privacy_score = Column(Float, nullable=False)
    trust_score = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=False)
    false_positive_rate = Column(Float, nullable=False)
    bias_risk = Column(Float, nullable=False)
