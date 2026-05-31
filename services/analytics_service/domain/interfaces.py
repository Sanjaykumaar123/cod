from abc import ABC, abstractmethod
from services.analytics_service.domain.models import AnalyticsSnapshot, TrendReport

class AnalyticsEngineInterface(ABC):
    @abstractmethod
    def generate_snapshot(self, tenant_id: str) -> AnalyticsSnapshot:
        """Aggregates multi-channel metrics into a static performance snapshot."""
        pass

    @abstractmethod
    def compile_trend_report(self, report_type: str, date_range: str, tenant_id: str) -> TrendReport:
        """Runs temporal query rollups to project detection trends and false positive rates."""
        pass
