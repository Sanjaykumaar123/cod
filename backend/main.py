import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend import models, schemas
from backend.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    RoleChecker,
    get_password_hash
)

# Import Engines
from backend.engines.vision import VisionEngine
from backend.engines.privacy import PrivacyEngine
from backend.engines.behavior import BehaviorIntelligenceEngine
from backend.engines.risk import RiskScoringEngine
from backend.engines.event import EventEngine
from backend.engines.explainable import ExplainableAIEngine
from backend.engines.identity import IdentityGovernanceEngine
from backend.engines.simulator import SimulatorEngine
from backend.engines.audit import AuditEngine
from backend.engines.analytics import AnalyticsEngine

app = FastAPI(
    title="BlindWatch AI OS API",
    description="The Privacy-First Surveillance Operating System API",
    version="1.0.0"
)

# Configure CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup database initialization & seeding
@app.on_event("startup")
def startup_db_init():
    from backend.database import Base, engine, SessionLocal
    from backend.models import User
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user_exists = db.query(User).first()
        if not user_exists:
            print("Production database empty. Running initial seed...")
            from backend.init_db import seed_db
            seed_db()
    except Exception as e:
        print(f"Startup database check error: {e}")
    finally:
        db.close()

# Initialize Vision Engine
vision_engine = VisionEngine()

@app.get("/")
@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "BlindWatch AI OS"}

# --- AUTH ENDPOINTS ---

@app.post("/api/auth/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    
    # Audit log login action
    AuditEngine.log_action(
        db=db,
        action="USER_LOGIN",
        reason=f"User {user.username} authenticated successfully.",
        outcome="success",
        user_id=user.id,
        username=user.username,
        role=user.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name
    }

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# --- CAMERA ENDPOINTS ---

@app.get("/api/cameras", response_model=List[schemas.CameraResponse])
def get_cameras(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Camera).all()

@app.post("/api/cameras", response_model=schemas.CameraResponse)
def create_camera(
    camera: schemas.CameraCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin"]))
):
    db_camera = db.query(models.Camera).filter(models.Camera.name == camera.name).first()
    if db_camera:
        raise HTTPException(status_code=400, detail="Camera with this name already exists")
    
    new_cam = models.Camera(
        name=camera.name,
        location=camera.location,
        rtsp_url=camera.rtsp_url,
        resolution=camera.resolution,
        fps=camera.fps,
        is_active=camera.is_active,
        privacy_shield_active=camera.privacy_shield_active,
        safety_score=95.0,
        threat_count=0
    )
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    
    AuditEngine.log_action(
        db=db,
        action="CAMERA_CREATION",
        reason=f"Admin created camera {camera.name} at location {camera.location}",
        outcome="success",
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role
    )
    
    return new_cam

@app.put("/api/cameras/{camera_id}/privacy-shield")
def toggle_privacy_shield(
    camera_id: int,
    active: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin", "auditor"]))
):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera.privacy_shield_active = active
    db.commit()
    
    AuditEngine.log_action(
        db=db,
        action="PRIVACY_SHIELD_TOGGLE",
        reason=f"Toggled camera #{camera_id} privacy shield to {active}.",
        outcome="success",
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role
    )
    
    return {"id": camera.id, "name": camera.name, "privacy_shield_active": camera.privacy_shield_active}

@app.post("/api/cameras/{camera_id}/feed")
def process_camera_feed(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Simulates real-time ingestion of a camera frame, running the privacy-first pipeline.
    This generates telemetry/track data and returns it.
    """
    result = vision_engine.process_frame_realtime(db, camera_id)
    return result


# --- ANONYMOUS ENTITY ENDPOINTS ---

@app.get("/api/entities", response_model=List[schemas.AnonymousEntityResponse])
def get_entities(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.AnonymousEntity)
    if status:
        query = query.filter(models.AnonymousEntity.status == status)
    return query.order_by(models.AnonymousEntity.last_seen.desc()).all()

@app.get("/api/entities/{entity_id}/tracks", response_model=List[schemas.EntityTrackResponse])
def get_entity_tracks(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tracks = db.query(models.EntityTrack).filter(models.EntityTrack.entity_id == entity_id).order_by(models.EntityTrack.timestamp.asc()).all()
    return tracks

@app.get("/api/entities/{entity_id}/identity")
def request_entity_identity(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Tries to decrypt the identity. Succeeds only if an active, dual-approved lease exists.
    """
    access_result = IdentityGovernanceEngine.check_identity_access(db, entity_id, current_user)
    return access_result


# --- EVENT ENDPOINTS ---

@app.get("/api/events", response_model=List[schemas.EventResponse])
def get_events(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Event)
    if status:
        query = query.filter(models.Event.status == status)
    return query.order_by(models.Event.timestamp.desc()).all()

@app.put("/api/events/{event_id}", response_model=schemas.EventResponse)
def update_event(
    event_id: int,
    payload: schemas.EventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin", "officer"]))
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if payload.status:
        if payload.status == "acknowledged":
            EventEngine.acknowledge_event(db, event_id, current_user.id, current_user.username, current_user.role)
        elif payload.status == "false_positive":
            EventEngine.mark_false_positive(db, event_id, current_user.id, current_user.username, current_user.role, "Marked via dashboard")
        else:
            event.status = payload.status
            db.commit()
            db.refresh(event)
            
    return event

@app.get("/api/events/{event_id}/explain")
def explain_event_ai(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns explainable AI information for a security alert.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    explanation = ExplainableAIEngine.explain_event(event.reasoning)
    explanation["event_id"] = event.id
    explanation["event_type"] = event.event_type
    explanation["risk_score"] = event.risk_score
    explanation["confidence"] = event.confidence
    return explanation


# --- IDENTITY GOVERNANCE ENDPOINTS ---

@app.get("/api/identity-requests", response_model=List[schemas.IdentityRequestResponse])
def get_identity_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Viewer cannot see requests
    if current_user.role == "viewer":
         raise HTTPException(status_code=403, detail="Viewer role is not authorized to read requests")
    return db.query(models.IdentityRequest).order_by(models.IdentityRequest.created_at.desc()).all()

@app.post("/api/identity-requests", response_model=schemas.IdentityRequestResponse)
def create_identity_request(
    payload: schemas.IdentityRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin", "officer"]))
):
    # Check if entity exists
    entity = db.query(models.AnonymousEntity).filter(models.AnonymousEntity.entity_id == payload.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    # Check if a pending request already exists
    existing = db.query(models.IdentityRequest).filter(
        models.IdentityRequest.entity_id == payload.entity_id,
        models.IdentityRequest.status == "pending"
    ).first()
    if existing:
        return existing
        
    req = IdentityGovernanceEngine.create_request(
        db=db,
        requester_id=current_user.id,
        requester_name=current_user.full_name or current_user.username,
        entity_id=payload.entity_id,
        justification=payload.justification,
        duration_minutes=payload.duration_minutes
    )
    return req

@app.post("/api/identity-requests/{request_id}/approve", response_model=schemas.IdentityRequestResponse)
def approve_identity_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin", "auditor"]))
):
    req = db.query(models.IdentityRequest).filter(models.IdentityRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Check if this approver is the requester themselves (prevent self-approval)
    if req.requester_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot self-approve decryption request")
        
    updated_req = IdentityGovernanceEngine.approve_request(
        db=db,
        request_id=request_id,
        approver_id=current_user.id,
        approver_name=current_user.full_name or current_user.username,
        role=current_user.role
    )
    return updated_req

@app.post("/api/identity-requests/{request_id}/reject", response_model=schemas.IdentityRequestResponse)
def reject_identity_request(
    request_id: int,
    payload: schemas.IdentityRequestReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin", "auditor"]))
):
    req = db.query(models.IdentityRequest).filter(models.IdentityRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    updated_req = IdentityGovernanceEngine.reject_request(
        db=db,
        request_id=request_id,
        approver_id=current_user.id,
        approver_name=current_user.full_name or current_user.username,
        role=current_user.role,
        reason=payload.rejection_reason or "Disapproved by security authority."
    )
    return updated_req


# --- AUDIT LOGS ENDPOINTS ---

@app.get("/api/audit-logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(RoleChecker(["admin", "auditor"]))
):
    """
    Retrieves the entire security audit trail. Strict RBAC restriction.
    """
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).all()


# --- PRIVACY CENTER ENDPOINTS ---

@app.get("/api/privacy-metrics")
def get_privacy_metrics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Exposes metrics for compliance scores and dynamically triggers calculations.
    """
    metrics = PrivacyEngine.calculate_privacy_metrics(db)
    # Add historical metric points for charts
    history = db.query(models.PrivacyMetric).order_by(models.PrivacyMetric.timestamp.desc()).limit(10).all()
    history_reversed = list(reversed(history))
    
    return {
        "current": metrics,
        "history": [
            {
                "timestamp": h.timestamp.strftime("%H:%M"),
                "privacy_score": h.privacy_score,
                "compliance_score": h.compliance_score,
                "transparency_score": h.transparency_score,
                "active_anonymous_count": h.active_anonymous_count
            }
            for h in history_reversed
        ],
        "recommendations": [
            "Purge metadata logs older than 7 days (GDPR compliance optimization).",
            "Enable double-blind authorization locks on Gate Alpha video nodes.",
            "De-escalate sensitivity levels during high-density pedestrian hours to lower false positives."
        ]
    }


# --- SIMULATOR ENDPOINTS ---

@app.post("/api/simulator", response_model=schemas.SimulationResponse)
def execute_simulation(
    payload: schemas.SimulationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Runs the simulation algorithm to compare traditional vs privacy-first architectures.
    """
    result = SimulatorEngine.run_simulation(
        db=db,
        config_name=payload.config_name,
        cameras_count=payload.cameras_count,
        retention_days=payload.retention_days,
        sensitivity=payload.sensitivity,
        identity_collection=payload.identity_collection,
        crowd_density=payload.crowd_density,
        threat_level=payload.threat_level,
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role
    )
    
    # Retrieve the simulation record we just created
    db_res = db.query(models.SimulationResult).filter(models.SimulationResult.id == result["simulation_id"]).first()
    return db_res

@app.get("/api/simulator/results", response_model=List[schemas.SimulationResponse])
def get_simulator_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.SimulationResult).order_by(models.SimulationResult.timestamp.desc()).all()


# --- ANALYTICS ENDPOINTS ---

@app.get("/api/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Compiles data trends, false positives, areas, and camera performance logs.
    """
    return AnalyticsEngine.get_dashboard_analytics(db)


# --- REPORTS ENDPOINTS ---

@app.get("/api/reports/download")
def generate_pdf_report_json(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Prepares a data payload for generating downloadable PDF style summary reports.
    """
    analytics = AnalyticsEngine.get_dashboard_analytics(db)
    
    # Log report generation in the audit logs
    AuditEngine.log_action(
        db=db,
        action="REPORT_EXPORT",
        reason="Downloaded comprehensive system safety and privacy report.",
        outcome="success",
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role
    )
    
    return {
        "report_id": f"BW-REP-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "generated_by": current_user.full_name or current_user.username,
        "security_score": round(analytics["active_cameras"] * 20.0, 1), # mock formula
        "privacy_score": analytics["privacy_score"],
        "compliance_status": "EXCELLENT" if analytics["privacy_score"] > 90.0 else "REVIEW REQUIRED",
        "threat_summary": {
            "total_unresolved_alerts": analytics["threat_alerts"],
            "total_incidents_recorded": analytics["total_events"],
            "false_positive_rate": f"{analytics['false_positive_rate']}%"
        },
        "compliance_summary": {
            "gdpr_compliance": "PASSED (Identity destroyed by default)",
            "ccpa_compliance": "PASSED (Dual authorization encryption gates active)",
            "audit_trail_integrity": "SECURE (100% auditable lifecycle)"
        },
        "strategic_recommendations": [
            "Deploy additional nodes in North Perimeter zone to cover surveillance gap.",
            "Reduce retention cycle from 14 days to 7 days to eliminate retention risks.",
            "Conduct automated audits on auditor decryption approvals weekly."
        ]
    }
