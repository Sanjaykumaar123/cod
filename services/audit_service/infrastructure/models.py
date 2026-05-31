from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from services.shared.database import Base, TenantMixin

class AuditLog(Base, TenantMixin):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    reason = Column(String(500), nullable=False)
    outcome = Column(String(50), default="success", nullable=False)
    ip_address = Column(String(100), default="127.0.0.1", nullable=True)
    hash = Column(String(256), nullable=True)
    previous_hash = Column(String(256), nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

class AuditSession(Base, TenantMixin):
    __tablename__ = 'audit_sessions'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_username = Column(String(100), nullable=False)
    login_time = Column(String(100), nullable=False)
    logout_time = Column(String(100), nullable=True)
    ip_address = Column(String(100), nullable=True)

class ApprovalHistory(Base, TenantMixin):
    __tablename__ = 'approval_history'

    id = Column(Integer, primary_key=True, index=True)
    petition_id = Column(String(100), index=True, nullable=False)
    requester_name = Column(String(100), nullable=False)
    approver_name = Column(String(100), nullable=False)
    role_signed = Column(String(50), nullable=False)
    signed_at = Column(String(100), nullable=False)
    status = Column(String(50), default="approved", nullable=False)
