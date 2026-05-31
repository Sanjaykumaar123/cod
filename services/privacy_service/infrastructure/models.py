from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from services.shared.database import Base, TenantMixin

class PrivacyMetric(Base, TenantMixin):
    __tablename__ = "privacy_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    privacy_score = Column(Float, default=100.0)
    compliance_score = Column(Float, default=100.0)
    transparency_score = Column(Float, default=100.0)
    retention_risk = Column(String(50), default="Low")
    exposure_risk = Column(String(50), default="Low")
    active_anonymous_count = Column(Integer, default=0)
    requests_denied = Column(Integer, default=0)
    requests_approved = Column(Integer, default=0)

class PrivacyScore(Base, TenantMixin):
    __tablename__ = 'privacy_scores'

    id = Column(Integer, primary_key=True, index=True)
    score_value = Column(Float, default=100.0, nullable=False)
    exposure_risk = Column(String(50), default="Low", nullable=False)
    dynamic_anonymization_rate = Column(Float, default=100.0, nullable=False)
    timestamp = Column(String(100), nullable=False)

class ComplianceRule(Base, TenantMixin):
    __tablename__ = 'compliance_rules'

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(100), unique=True, index=True, nullable=False)
    regulation_name = Column(String(255), nullable=False)
    is_enforced = Column(Boolean, default=True, nullable=False)
    settings_meta = Column(JSON, nullable=True)

class PrivacyEvent(Base, TenantMixin):
    __tablename__ = 'privacy_events'

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    severity = Column(String(50), default="Low", nullable=False)
    timestamp = Column(String(100), nullable=False)
