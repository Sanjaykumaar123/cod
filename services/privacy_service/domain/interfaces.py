from abc import ABC, abstractmethod
from services.privacy_service.domain.models import PrivacyScore, ComplianceRule, PrivacyEvent

class PrivacyComplianceInterface(ABC):
    @abstractmethod
    def calculate_privacy_index(self, tenant_id: str) -> PrivacyScore:
        """Evaluates active retention records and generates global compliance ratings."""
        pass

    @abstractmethod
    def anonymize_frame_biometrics(self, image_raw: bytes, bounding_boxes: list[list[int]]) -> bytes:
        """Applies Gaussian Blur overlay to biometric sectors (faces)."""
        pass

    @abstractmethod
    def execute_retention_purge(self, compliance_rule: ComplianceRule, tenant_id: str) -> list[PrivacyEvent]:
        """Deletes video and coordinate logs exceeding compliance limits."""
        pass
