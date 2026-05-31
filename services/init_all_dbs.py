from services.shared.database import Base, engine

# Import all models to register them on Base.metadata
from services.auth_service.infrastructure import models as auth_models
from services.camera_service.infrastructure import models as camera_models
from services.vision_service.infrastructure import models as vision_models
from services.privacy_service.infrastructure import models as privacy_models
from services.event_service.infrastructure import models as event_models
from services.audit_service.infrastructure import models as audit_models
from services.analytics_service.infrastructure import models as analytics_models
from services.simulator_service.infrastructure import models as simulator_models
from services.identity_governance_service.infrastructure import models as gov_models

def init_databases():
    print("Initializing modular databases...")
    Base.metadata.create_all(bind=engine)
    print("All service tables created successfully.")

if __name__ == "__main__":
    init_databases()
