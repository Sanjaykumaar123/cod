class AnalyticsSnapshot:
    def __init__(self, snapshot_id: str, threat_count: int, active_cameras: int, avg_privacy_score: float, timestamp: str, tenant_id: str):
        self.snapshot_id = snapshot_id
        self.threat_count = threat_count
        self.active_cameras = active_cameras
        self.avg_privacy_score = avg_privacy_score
        self.timestamp = timestamp
        self.tenant_id = tenant_id

class TrendReport:
    def __init__(self, report_id: str, report_type: str, data_points: list[dict], generated_at: str, tenant_id: str):
        self.report_id = report_id
        self.report_type = report_type
        self.data_points = data_points
        self.generated_at = generated_at
        self.tenant_id = tenant_id
