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

# Entrypoint for uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
