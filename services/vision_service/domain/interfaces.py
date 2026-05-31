from abc import ABC, abstractmethod
from services.vision_service.domain.models import VisionJob, Detection, EntityTrack

class VisionProcessingInterface(ABC):
    @abstractmethod
    def start_vision_pipeline(self, camera_name: str, run_mode: str, tenant_id: str) -> VisionJob:
        """Starts a background frame listener loop on target camera."""
        pass

    @abstractmethod
    def process_frame(self, frame_bytes: bytes, tenant_id: str) -> list[Detection]:
        """Runs model inference on raw pixel inputs and extracts entities."""
        pass

    @abstractmethod
    def track_coordinates(self, detections: list[Detection], tenant_id: str) -> list[EntityTrack]:
        """Maps temporal coordinates to maintain paths for active anonymous IDs."""
        pass
