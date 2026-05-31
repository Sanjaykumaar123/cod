class SimulationRun:
    def __init__(self, run_id: str, scenario_name: str, run_parameters: dict, timestamp: str, tenant_id: str):
        self.run_id = run_id
        self.scenario_name = scenario_name
        self.run_parameters = run_parameters
        self.timestamp = timestamp
        self.tenant_id = tenant_id

class SimulationResult:
    def __init__(self, run_id: str, projected_privacy_score: float, projected_threats_caught: int, compliance_grade: str, tenant_id: str):
        self.run_id = run_id
        self.projected_privacy_score = projected_privacy_score
        self.projected_threats_caught = projected_threats_caught
        self.compliance_grade = compliance_grade
        self.tenant_id = tenant_id
