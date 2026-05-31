class PrivacyScore:
    def __init__(self, score_value: float, exposure_risk: str, dynamic_anonymization_rate: float, timestamp: str, tenant_id: str):
        self.score_value = score_value
        self.exposure_risk = exposure_risk
        self.dynamic_anonymization_rate = dynamic_anonymization_rate
        self.timestamp = timestamp
        self.tenant_id = tenant_id

class ComplianceRule:
    def __init__(self, rule_code: str, regulation_name: str, is_enforced: bool, settings_meta: dict, tenant_id: str):
        self.rule_code = rule_code
        self.regulation_name = regulation_name
        self.is_enforced = is_enforced
        self.settings_meta = settings_meta
        self.tenant_id = tenant_id

class PrivacyEvent:
    def __init__(self, event_type: str, description: str, severity: str, timestamp: str, tenant_id: str):
        self.event_type = event_type
        self.description = description
        self.severity = severity
        self.timestamp = timestamp
        self.tenant_id = tenant_id
