from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from services.shared.database import Base, BaseMixin, SoftDeleteMixin, GUID
import datetime

class IdentityRequest(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = 'identity_requests'

    event_id = Column(GUID, nullable=True)
    requester_id = Column(GUID, nullable=True)
    justification = Column(Text, nullable=False)
    case_number = Column(String(100), nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, AUDITOR_APPROVED, ADMIN_APPROVED, REJECTED, COMPLETED
    requested_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Legacy attributes for compatibility
    request_id = Column(String(100), unique=True, index=True, nullable=True)
    requester_name = Column(String(100), nullable=True)
    entity_id = Column(String(100), index=True, nullable=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    approved_by_auditor = Column(Boolean, default=False, nullable=False)
    approved_by_admin = Column(Boolean, default=False, nullable=False)
    encrypted_identity = Column(String(1000), nullable=True)
    auditor_key_share = Column(String(500), nullable=True)
    admin_key_share = Column(String(500), nullable=True)
    decrypted_identity = Column(String(255), nullable=True)

    approvals = relationship('Approval', back_populates='request')
    sessions = relationship('IdentityRevealSession', back_populates='request')

class Approval(Base, BaseMixin):
    __tablename__ = 'approvals'

    request_id = Column(GUID, ForeignKey('identity_requests.id', ondelete='CASCADE'), nullable=True)
    approver_id = Column(GUID, nullable=True)
    approval_stage = Column(String(50), nullable=True)
    decision = Column(String(20), default="APPROVED", nullable=False)
    comments = Column(Text, nullable=True)
    approved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Legacy attributes for compatibility
    approval_id = Column(String(100), unique=True, index=True, nullable=True)
    legacy_request_id = Column(String(100), nullable=True)
    approver_name = Column(String(100), nullable=True)
    signed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    request = relationship('IdentityRequest', back_populates='approvals')

class IdentityRevealSession(Base, BaseMixin):
    __tablename__ = 'identity_reveal_sessions'

    request_id = Column(GUID, ForeignKey('identity_requests.id', ondelete='CASCADE'), nullable=True)
    revealed_by = Column(GUID, nullable=True)
    expires_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String(20), default="active", nullable=False)

    # Legacy attributes for compatibility
    reveal_id = Column(String(100), unique=True, index=True, nullable=True)
    decrypted_identity = Column(String(255), nullable=True)

    request = relationship('IdentityRequest', back_populates='sessions')
