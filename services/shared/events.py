from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class EventBase(BaseModel):
    tenant_id: str
    timestamp: str

class CameraFrameProcessed(EventBase):
    job_id: str
    camera_name: str
    frame_metadata: Dict[str, Any]

class EntityDetected(EventBase):
    entity_id: str
    x: int
    y: int
    speed: float
    location: str
    anomalies_found: List[str]

class ThreatAlertEmitted(EventBase):
    event_id: str
    event_type: str
    location: str
    risk_score: float
    confidence: float
    reasoning_summary: str

class MetricsUpdateEvent(EventBase):
    metric_type: str
    delta: float

class AuditLogLogged(EventBase):
    action: str
    username: str
    role: str
    outcome: str
    reason: str

class IdentityDecryptPetition(EventBase):
    petition_id: str
    requester_name: str
    entity_id: str
    status: str
    expires_at: Optional[str] = None
