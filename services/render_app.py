import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize monolithic app for constrained cloud environments (Render Free Tier)
app = FastAPI(
    title="BlindWatch AI - Cloud Monolith",
    description="Unified API for Render deployment to stay under 512MB RAM.",
    version="2.0.0"
)

# Set up global CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Render handles routing, wildcard is acceptable for this fallback
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import all microservice apps
from services.auth_service.main import app as auth_app
from services.camera_service.main import app as camera_app
from services.vision_service.main import app as vision_app
from services.privacy_service.main import app as privacy_app
from services.event_service.main import app as event_app
from services.audit_service.main import app as audit_app
from services.analytics_service.main import app as analytics_app
from services.simulator_service.main import app as simulator_app
from services.identity_governance_service.main import app as identity_app

# Combine all routes into the single ASGI application
app.include_router(auth_app.router)
app.include_router(camera_app.router)
app.include_router(vision_app.router)
app.include_router(privacy_app.router)
app.include_router(event_app.router)
app.include_router(audit_app.router)
app.include_router(analytics_app.router)
app.include_router(simulator_app.router)
app.include_router(identity_app.router)

# Port WebSockets from gateway
from services.gateway import app as gateway_app
for route in gateway_app.routes:
    if getattr(route, "name", "") != "route_request":
        app.routes.append(route)

@app.get("/")
def root():
    return {"status": "online", "mode": "cloud_monolith"}

from services.demo_seeder import seed_demo_data
import asyncio
from fastapi import BackgroundTasks

@app.post("/api/v1/demo/seed")
def seed_demo():
    """Volume 6 - Seed intelligence layer with realistic data."""
    return seed_demo_data()

@app.post("/api/v1/demo/incident")
def trigger_security_incident(background_tasks: BackgroundTasks):
    """Executive Demo Mode: Run Full Security Incident in 30 seconds."""
    # We can broadcast to WebSockets, but for now we simply create the audit and event trails.
    from services.shared.database import SessionLocal
    from services.event_service.infrastructure.models import Event
    from services.audit_service.infrastructure.models import AuditLog
    import datetime
    import uuid

    def run_incident():
        db = SessionLocal()
        try:
            # Step 1: Suspicious Entity Detected
            evt1 = Event(
                event_type="Perimeter Breach",
                severity="HIGH",
                reasoning="Entity scaled Sector B fence. Behavior escalating.",
                camera_id=str(uuid.uuid4()),
                risk_score=95.5,
                tenant_id="default"
            )
            evt1.created_at = datetime.datetime.utcnow()
            db.add(evt1)
            
            # Step 2: AI Detection Log
            log1 = AuditLog(
                user_id=str(uuid.uuid4()),
                action="THREAT_DETECTED",
                target_type="System",
                reason="AI Threat Engine activated. Automated lock-down suggested.",
                ip_address="10.0.0.1",
                tenant_id="default"
            )
            db.add(log1)
            db.commit()
            
            # Step 3 (Simulated delay): Governance Request
            # Real implementation would await asyncio.sleep(5) and broadcast.
        finally:
            db.close()

    background_tasks.add_task(run_incident)
    return {"status": "incident_started", "message": "Executive Demo sequence initiated. Events are generating."}

# Entrypoint for uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
