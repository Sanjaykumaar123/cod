from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from services.shared.database import Base, TenantMixin

class IdentityRequest(Base, TenantMixin):
    __tablename__ = 'identity_requests'

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    requester_id = Column(Integer, nullable=True)
    requester_name = Column(String(100), nullable=False)
    entity_id = Column(String(100), index=True, nullable=False)
    justification = Column(String(500), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    approved_by_auditor = Column(Boolean, default=False, nullable=False)
    approved_by_admin = Column(Boolean, default=False, nullable=False)
    encrypted_identity = Column(String(1000), nullable=True)
    auditor_key_share = Column(String(500), nullable=True)
    admin_key_share = Column(String(500), nullable=True)
    decrypted_identity = Column(String(255), nullable=True)

class Approval(Base, TenantMixin):
    __tablename__ = 'approvals'

    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(String(100), unique=True, index=True, nullable=False)
    request_id = Column(String(100), ForeignKey('identity_requests.request_id', ondelete='CASCADE'), nullable=False)
    approver_name = Column(String(100), nullable=False)
    signed_at = Column(DateTime, default=func.now(), nullable=False)

    request = relationship('IdentityRequest')

class IdentityRevealSession(Base, TenantMixin):
    __tablename__ = 'identity_reveal_sessions'

    id = Column(Integer, primary_key=True, index=True)
    reveal_id = Column(String(100), unique=True, index=True, nullable=False)
    request_id = Column(String(100), ForeignKey('identity_requests.request_id', ondelete='CASCADE'), nullable=False)
    decrypted_identity = Column(String(255), nullable=False)  # Encrypted at rest in production
    expires_at = Column(String(100), nullable=False)

    request = relationship('IdentityRequest')
