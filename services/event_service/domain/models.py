class ThreatEvent:
    def __init__(self, event_id: str, event_type: str, location: str, entity_id: str, risk_score: float, confidence: float, status: str, timestamp: str, tenant_id: str):
        self.event_id = event_id
        self.event_type = event_type
        self.location = location
        self.entity_id = entity_id
        self.risk_score = risk_score
        self.confidence = confidence
        self.status = status
        self.timestamp = timestamp
        self.tenant_id = tenant_id

class ThreatEvidence:
    def __init__(self, event_id: str, image_snapshot_url: str, video_clip_url: str, encryption_meta: dict, tenant_id: str):
        self.event_id = event_id
        self.image_snapshot_url = image_snapshot_url
        self.video_clip_url = video_clip_url
        self.encryption_meta = encryption_meta
        self.tenant_id = tenant_id

class ThreatTimeline:
    def __init__(self, event_id: str, events_sequence: list[dict], tenant_id: str):
        self.event_id = event_id
        self.events_sequence = events_sequence
        self.tenant_id = tenant_id
