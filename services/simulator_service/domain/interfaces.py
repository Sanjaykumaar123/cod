from abc import ABC, abstractmethod
from services.simulator_service.domain.models import SimulationRun, SimulationResult

class SimulationEngineInterface(ABC):
    @abstractmethod
    def trigger_scenario_run(self, scenario_name: str, parameters: dict, tenant_id: str) -> SimulationRun:
        """Schedules a policy test instance with custom rules."""
        pass

    @abstractmethod
    def compute_projection(self, run_id: str, tenant_id: str) -> SimulationResult:
        """Simulates camera streams under different configurations to project scores."""
        pass
