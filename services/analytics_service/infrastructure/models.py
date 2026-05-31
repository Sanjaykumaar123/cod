from sqlalchemy import Column, Integer, String, Float, JSON
from services.shared.database import Base, TenantMixin

class AnalyticsSnapshot(Base, TenantMixin):
    __tablename__ = 'analytics_snapshots'

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(String(100), unique=True, index=True, nullable=False)
    threat_count = Column(Integer, default=0, nullable=False)
    active_cameras = Column(Integer, default=0, nullable=False)
    avg_privacy_score = Column(Float, default=100.0, nullable=False)
    timestamp = Column(String(100), nullable=False)

class TrendReport(Base, TenantMixin):
    __tablename__ = 'trend_reports'

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(100), unique=True, index=True, nullable=False)
    report_type = Column(String(100), nullable=False)
    data_points = Column(JSON, nullable=False)  # Stores aggregated metrics history
    generated_at = Column(String(100), nullable=False)
