from sqlalchemy import Column, String, Float, DateTime, Text, Integer
from services.shared.database import Base, BaseMixin, GUID
import datetime

class PrivacyMetric(Base, BaseMixin):
    __tablename__ = "privacy_metrics"
    
    privacy_score = Column(Float, default=100.0)
    compliance_score = Column(Float, default=100.0)
    transparency_score = Column(Float, default=100.0)
    retention_risk = Column(String(50), default="Low")
    exposure_risk = Column(String(50), default="Low")
    active_anonymous_count = Column(Integer, default=0)
    requests_denied = Column(Integer, default=0)
    requests_approved = Column(Integer, default=0)

class PrivacyScore(Base, BaseMixin):
    __tablename__ = 'privacy_scores'

    privacy_score = Column(Float, default=100.0, nullable=False)
    identity_storage_penalty = Column(Float, default=0.0, nullable=False)
    retention_penalty = Column(Float, default=0.0, nullable=False)
    sharing_penalty = Column(Float, default=0.0, nullable=False)
    tracking_penalty = Column(Float, default=0.0, nullable=False)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class ComplianceRule(Base, BaseMixin):
    __tablename__ = 'compliance_rules'

    rule_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="medium", nullable=False)

class ExposureRisk(Base, BaseMixin):
    __tablename__ = 'exposure_risks'

    risk_type = Column(String(100), nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    recommendation = Column(Text, nullable=True)
