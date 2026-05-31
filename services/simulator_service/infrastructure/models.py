from sqlalchemy import Column, String, Float, ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from services.shared.database import Base, BaseMixin, GUID
import datetime

class SimulationRun(Base, BaseMixin):
    __tablename__ = 'simulation_runs'

    scenario_name = Column(String(255), nullable=False)
    camera_count = Column(Integer, default=0, nullable=False)
    retention_days = Column(Integer, default=14, nullable=False)
    identity_storage = Column(Boolean, default=False, nullable=False)
    sensitivity = Column(Float, default=0.5, nullable=False)
    created_by = Column(GUID, nullable=True)

    results = relationship('SimulationResult', back_populates='run')

class SimulationResult(Base, BaseMixin):
    __tablename__ = 'simulation_results'

    run_id = Column(GUID, ForeignKey('simulation_runs.id', ondelete='CASCADE'), nullable=True)
    privacy_score = Column(Float, default=100.0, nullable=False)
    safety_score = Column(Float, default=100.0, nullable=False)
    trust_score = Column(Float, default=100.0, nullable=False)
    compliance_score = Column(Float, default=100.0, nullable=False)
    false_positive_rate = Column(Float, default=0.0, nullable=False)
    bias_risk = Column(Float, default=0.0, nullable=False)

    # Legacy attributes for compatibility
    config_name = Column(String(100), nullable=True)
    cameras_count = Column(Integer, nullable=True)
    retention_days = Column(Integer, nullable=True)
    sensitivity = Column(Float, nullable=True)
    identity_collection = Column(String(100), nullable=True)
    crowd_density = Column(String(50), nullable=True)
    threat_level = Column(String(50), nullable=True)
    
    traditional_safety_score = Column(Float, default=70.0)
    blindwatch_safety_score = Column(Float, default=95.0)
    traditional_privacy_score = Column(Float, default=20.0)
    blindwatch_privacy_score = Column(Float, default=98.0)
    recommendations = Column(String(1000), nullable=True)

    run = relationship('SimulationRun', back_populates='results')
