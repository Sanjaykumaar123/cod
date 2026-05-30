from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: str
    role: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    full_name: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Camera schemas
class CameraBase(BaseModel):
    name: str
    location: str
    rtsp_url: Optional[str] = None
    resolution: Optional[str] = "1080p"
    fps: Optional[int] = 30
    is_active: Optional[bool] = True
    privacy_shield_active: Optional[bool] = True

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: int
    status: str
    safety_score: float
    threat_count: int

    class Config:
        from_attributes = True

# AnonymousEntity schemas
class AnonymousEntityBase(BaseModel):
    entity_id: str
    last_location: str
    risk_score: float
    status: str

class AnonymousEntityResponse(AnonymousEntityBase):
    id: int
    first_seen: datetime
    last_seen: datetime
    behavior_signature: Optional[str] = None
    movement_profile: Optional[str] = None
    zone_profile: Optional[str] = None
    object_profile: Optional[str] = None
    duration_profile: Optional[str] = None

    class Config:
        from_attributes = True

# EntityTrack schemas
class EntityTrackResponse(BaseModel):
    id: int
    entity_id: str
    timestamp: datetime
    location_x: int
    location_y: int
    zone: str
    risk_score: float
    speed: float

    class Config:
        from_attributes = True

# Event schemas
class EventBase(BaseModel):
    event_type: str
    location: str
    entity_id: Optional[str] = None
    risk_score: float
    confidence: float
    evidence_image: Optional[str] = None
    reasoning: str
    timeline: Optional[str] = None
    status: Optional[str] = "unresolved"
    is_false_positive: Optional[bool] = False

class EventResponse(EventBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class EventUpdate(BaseModel):
    status: Optional[str] = None
    is_false_positive: Optional[bool] = None

# IdentityRequest schemas
class IdentityRequestCreate(BaseModel):
    entity_id: str
    justification: str
    duration_minutes: int = 30

class IdentityRequestReview(BaseModel):
    approve: bool
    rejection_reason: Optional[str] = None

class IdentityRequestResponse(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    entity_id: str
    justification: str
    status: str
    duration_minutes: int
    created_at: datetime
    approved_by_auditor: bool
    approved_by_admin: bool
    approved_by_auditor_name: Optional[str] = None
    approved_by_admin_name: Optional[str] = None
    expires_at: Optional[datetime] = None
    decrypted_identity: Optional[str] = None

    class Config:
        from_attributes = True

# AuditLog schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    action: str
    reason: str
    timestamp: datetime
    outcome: str
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True

# PrivacyMetric schemas
class PrivacyMetricResponse(BaseModel):
    id: int
    timestamp: datetime
    privacy_score: float
    compliance_score: float
    transparency_score: float
    retention_risk: str
    exposure_risk: str
    active_anonymous_count: int
    requests_denied: int
    requests_approved: int

    class Config:
        from_attributes = True

# Simulator schemas
class SimulationRequest(BaseModel):
    config_name: str
    cameras_count: int
    retention_days: int
    sensitivity: float
    identity_collection: str # default_anonymized, stored_by_default
    crowd_density: str # low, medium, high
    threat_level: str  # low, medium, high

class SimulationResponse(BaseModel):
    id: int
    timestamp: datetime
    config_name: str
    cameras_count: int
    retention_days: int
    sensitivity: float
    identity_collection: str
    crowd_density: str
    threat_level: str
    safety_score: float
    privacy_score: float
    trust_score: float
    compliance_score: float
    false_positive_rate: float
    bias_risk: float

    class Config:
        from_attributes = True
