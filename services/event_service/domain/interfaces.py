from abc import ABC, abstractmethod
from services.event_service.domain.models import ThreatEvent, ThreatEvidence, ThreatTimeline

class ThreatDetectionInterface(ABC):
    @abstractmethod
    def evaluate_threat(self, entity_track_data: dict, tenant_id: str) -> ThreatEvent | None:
        """Runs risk engines on trajectories to classify anomalous events."""
        pass

    @abstractmethod
    def attach_evidence_snapshot(self, event_id: str, image_bytes: bytes, tenant_id: str) -> ThreatEvidence:
        """Stores encrypted blurred snapshots inside object storage nodes."""
        pass

    @abstractmethod
    def build_event_timeline(self, event_id: str, tenant_id: str) -> ThreatTimeline:
        """Compiles trace logs into a human-readable and explainable sequence."""
        pass
