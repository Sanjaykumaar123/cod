from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Integer, Date, Text, JSON
from services.shared.database import Base, BaseMixin, SoftDeleteMixin, GUID
import datetime

class AnalyticsSnapshot(Base, BaseMixin):
    __tablename__ = 'analytics_snapshots'

    snapshot_date = Column(Date, default=datetime.date.today, nullable=False)
    total_events = Column(Integer, default=0, nullable=False)
    high_risk_events = Column(Integer, default=0, nullable=False)
    privacy_score = Column(Float, default=100.0, nullable=False)
    false_positive_rate = Column(Float, default=0.0, nullable=False)
    camera_health = Column(Float, default=100.0, nullable=False)

    # Backward compatibility properties
    @property
    def snapshot_id(self) -> str:
        return str(self.id)
    
    @property
    def threat_count(self) -> int:
        return self.total_events
    @threat_count.setter
    def threat_count(self, val: int):
        self.total_events = val

    @property
    def active_cameras(self) -> int:
        return 10
        
    @property
    def avg_privacy_score(self) -> float:
        return self.privacy_score
    @avg_privacy_score.setter
    def avg_privacy_score(self, val: float):
        self.privacy_score = val

    @property
    def timestamp(self) -> str:
        return self.snapshot_date.isoformat()

class ThreatTrend(Base, BaseMixin):
    __tablename__ = 'threat_trends'

    event_type = Column(String(100), nullable=False)
    count = Column(Integer, default=0, nullable=False)
    trend_direction = Column(String(20), default="stable", nullable=False)

class Report(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = 'reports'

    report_type = Column(String(50), nullable=False)
    generated_by = Column(GUID, nullable=True)
    file_url = Column(Text, nullable=False)

class TrendReport(Base, BaseMixin):
    __tablename__ = 'trend_reports'

    report_type = Column(String(100), nullable=False)
    data_points = Column(JSON, nullable=True)
    generated_at = Column(String(100), nullable=False)

    @property
    def report_id(self) -> str:
        return str(self.id)
