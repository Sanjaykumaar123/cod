from abc import ABC, abstractmethod
from services.camera_service.domain.models import Camera, CameraGroup, CameraHealth

class CameraManagerInterface(ABC):
    @abstractmethod
    def register_camera(self, camera_data: dict, tenant_id: str) -> Camera:
        """Registers a new camera entity under tenant boundaries."""
        pass

    @abstractmethod
    def test_rtsp_connection(self, rtsp_url: str) -> bool:
        """Validates network handshake with RTSP edge endpoint."""
        pass

    @abstractmethod
    def run_health_ping(self, camera_name: str, tenant_id: str) -> CameraHealth:
        """Pings stream port and compiles latency and connection status."""
        pass

    @abstractmethod
    def toggle_privacy_shield(self, camera_name: str, active: bool, tenant_id: str) -> Camera:
        """Enables or disables the physical pixel obscuring shield."""
        pass
