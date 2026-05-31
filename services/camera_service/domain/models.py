class Camera:
    def __init__(self, name: str, location: str, rtsp_url: str, resolution: str, fps: int, is_active: bool, privacy_shield_active: bool, tenant_id: str):
        self.name = name
        self.location = location
        self.rtsp_url = rtsp_url
        self.resolution = resolution
        self.fps = fps
        self.is_active = is_active
        self.privacy_shield_active = privacy_shield_active
        self.tenant_id = tenant_id

class CameraGroup:
    def __init__(self, name: str, description: str, cameras: list[Camera], tenant_id: str):
        self.name = name
        self.description = description
        self.cameras = cameras
        self.tenant_id = tenant_id

class CameraHealth:
    def __init__(self, camera_name: str, status: str, last_heartbeat: str, issues: list[str], tenant_id: str):
        self.camera_name = camera_name
        self.status = status
        self.last_heartbeat = last_heartbeat
        self.issues = issues
        self.tenant_id = tenant_id
