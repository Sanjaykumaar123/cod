from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from services.shared.database import Base, BaseMixin, GUID
import datetime

class AuditLog(Base, BaseMixin):
    __tablename__ = 'audit_logs'

    user_id = Column(GUID, nullable=True)
    action = Column(String(255), nullable=False)
    target_type = Column(String(255), nullable=True)
    target_id = Column(GUID, nullable=True)
    reason = Column(Text, nullable=False)
    result = Column(String(50), default="success", nullable=False)
    ip_address = Column(String(50), default="127.0.0.1", nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Cryptographic integrity fields
    hash = Column(String(256), nullable=True)
    previous_hash = Column(String(256), nullable=True)
    
    # Backward compatibility properties
    @property
    def outcome(self) -> str:
        return self.result
    @outcome.setter
    def outcome(self, value: str):
        self.result = value

    @property
    def username(self) -> str:
        return "admin_user"
    @username.setter
    def username(self, value: str):
        pass

    @property
    def role(self) -> str:
        return "auditor"
    @role.setter
    def role(self, value: str):
        pass

class AuditSession(Base, BaseMixin):
    __tablename__ = 'audit_sessions'

    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_username = Column(String(100), nullable=False)
    login_time = Column(String(100), nullable=False)
    logout_time = Column(String(100), nullable=True)
    ip_address = Column(String(100), nullable=True)

class ApprovalHistory(Base, BaseMixin):
    __tablename__ = 'approval_history'

    petition_id = Column(String(100), index=True, nullable=False)
    requester_name = Column(String(100), nullable=False)
    approver_name = Column(String(100), nullable=False)
    role_signed = Column(String(50), nullable=False)
    signed_at = Column(String(100), nullable=False)
    status = Column(String(50), default="approved", nullable=False)
