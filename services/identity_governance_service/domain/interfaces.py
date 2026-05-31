from abc import ABC, abstractmethod
from services.identity_governance_service.domain.models import IdentityRequest, Approval, IdentityRevealSession

class IdentityGovernanceInterface(ABC):
    @abstractmethod
    def create_petition(self, entity_id: str, requester_name: str, justification: str, duration_minutes: int, tenant_id: str) -> IdentityRequest:
        """Submits a new formal request for biometric decryption access."""
        pass

    @abstractmethod
    def sign_approval(self, request_id: str, approver_name: str, role: str, tenant_id: str) -> Approval:
        """Applies a legal authorization signature to a pending petition."""
        pass

    @abstractmethod
    def initiate_reveal_session(self, request_id: str, admin_key_bytes: bytes, auditor_key_bytes: bytes, tenant_id: str) -> IdentityRevealSession:
        """Cryptographically combines sharded key pairs to decrypt and display biometric identity."""
        pass
