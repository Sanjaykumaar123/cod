from sqlalchemy import Column, Integer, String, Float, JSON
from services.shared.database import Base, TenantMixin

class SimulationRun(Base, TenantMixin):
    __tablename__ = 'simulation_runs'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), unique=True, index=True, nullable=False)
    scenario_name = Column(String(100), nullable=False)
    run_parameters = Column(JSON, nullable=False)
    timestamp = Column(String(100), nullable=False)

class SimulationResult(Base, TenantMixin):
    __tablename__ = 'simulation_results'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), index=True, nullable=False)
    projected_privacy_score = Column(Float, nullable=False)
    projected_threats_caught = Column(Integer, nullable=False)
    compliance_grade = Column(String(50), default="A", nullable=False)
