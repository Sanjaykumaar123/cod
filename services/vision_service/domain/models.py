class VisionJob:
    def __init__(self, job_id: str, camera_name: str, status: str, run_mode: str, tenant_id: str):
        self.job_id = job_id
        self.camera_name = camera_name
        self.status = status
        self.run_mode = run_mode
        self.tenant_id = tenant_id

class Detection:
    def __init__(self, detection_id: str, entity_id: str, location: str, confidence: float, object_class: str, timestamp: str, tenant_id: str):
        self.detection_id = detection_id
        self.entity_id = entity_id
        self.location = location
        self.confidence = confidence
        self.object_class = object_class
        self.timestamp = timestamp
        self.tenant_id = tenant_id

class EntityTrack:
    def __init__(self, entity_id: str, coordinate_path: list[dict], current_speed: float, last_seen: str, tenant_id: str):
        self.entity_id = entity_id
        self.coordinate_path = coordinate_path
        self.current_speed = current_speed
        self.last_seen = last_seen
        self.tenant_id = tenant_id
