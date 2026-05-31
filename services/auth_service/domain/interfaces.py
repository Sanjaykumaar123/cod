from abc import ABC, abstractmethod
from services.auth_service.domain.models import User, Session

class AuthManagerInterface(ABC):
    @abstractmethod
    def authenticate_user(self, username: str, password_plain: str, tenant_id: str) -> User:
        """Verifies credentials and returns User if valid, raises exception if not."""
        pass

    @abstractmethod
    def generate_access_token(self, user: User) -> str:
        """Generates a secure access JWT."""
        pass

    @abstractmethod
    def verify_access_token(self, token: str) -> dict:
        """Decodes and validates a JWT, returning the payload mapping."""
        pass

    @abstractmethod
    def refresh_session_token(self, session: Session) -> Session:
        """Refreshes the dynamic session expiration boundary."""
        pass

    @abstractmethod
    def setup_mfa(self, username: str, tenant_id: str) -> dict:
        """Generates MFA provisioning parameters (TOTP keys)."""
        pass
