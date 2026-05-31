from abc import ABC, abstractmethod
from services.audit_service.domain.models import AuditLog, AuditSession, ApprovalHistory

class AuditLedgerInterface(ABC):
    @abstractmethod
    def log_action(self, username: str, role: str, action: str, reason: str, outcome: str, tenant_id: str) -> AuditLog:
        """Appends an operational log to the ledger."""
        pass

    @abstractmethod
    def start_session(self, username: str, ip_address: str, tenant_id: str) -> AuditSession:
        """Registers a portal session init event."""
        pass

    @abstractmethod
    def record_decryption_signature(self, petition_id: str, approver_name: str, role_signed: str, tenant_id: str) -> ApprovalHistory:
        """Logs cryptographic key signature events for legal petitions."""
        pass
