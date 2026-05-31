import os
import random
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean
from jose import jwt, JWTError

from services.shared.database import get_db, Base, engine, SessionLocal, TenantMixin

from services.event_service.infrastructure.models import Event

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

app = FastAPI(title="BlindWatch Event Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token claims")

@app.on_event("startup")
def seed_events():

    db = SessionLocal()
    try:
        if not db.query(Event).first():
            print("Seeding default events in modular db...")
            default_events = [
                ("Possible Intrusion", "West Corridor Hallway", "Entity_4102", 65.0, 0.89, "Entity detected entering restricted sector without clearance tokens."),
                ("Possible Violence", "South Perimeter Fence", "Entity_9932", 85.0, 0.95, "Erratic running patterns matching security alert signature."),
            ]
            for t, l, ent, risk, conf, reason in default_events:
                evt = Event(
                    event_type=t,
                    location=l,
                    entity_id=ent,
                    risk_score=risk,
                    confidence=conf,
                    reasoning=reason,
                    status="unresolved",
                    is_false_positive=False,
                    tenant_id="default"
                )
                db.add(evt)
            db.commit()
            print("Events seeded.")
    finally:
        db.close()

@app.get("/api/v1/events")
def get_events_v1(status: Optional[str] = None, severity: Optional[str] = None, event_type: Optional[str] = None, date: Optional[str] = None, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    query = db.query(Event).filter(Event.tenant_id == tenant_id, Event.is_deleted == False)
    if status:
        query = query.filter(Event.status == status)
    if severity:
        query = query.filter(Event.severity == severity)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    return query.order_by(Event.created_at.desc()).all()

@app.get("/api/v1/events/{id}")
def get_event_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    evt = db.query(Event).filter(Event.id == id, Event.tenant_id == tenant_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt

@app.post("/api/v1/events/{id}/escalate")
def escalate_event_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id = claims.get("user_id")
    evt = db.query(Event).filter(Event.id == id, Event.tenant_id == tenant_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
        
    evt.status = "ESCALATED"
    db.commit()
    db.refresh(evt)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "event.escalate", "Event", evt.id, f"Escalated event {evt.id} to active security queue.")
    
    return {"status": "success", "message": f"Event {evt.id} escalated successfully.", "event": evt}

@app.post("/api/v1/events/{id}/dismiss")
def dismiss_event_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id = claims.get("user_id")
    evt = db.query(Event).filter(Event.id == id, Event.tenant_id == tenant_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
        
    evt.status = "DISMISSED"
    evt.is_false_positive = True
    db.commit()
    db.refresh(evt)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "event.dismiss", "Event", evt.id, f"Dismissed event {evt.id} as false positive.")
    
    return {"status": "success", "message": f"Event {evt.id} dismissed.", "event": evt}

@app.get("/api/v1/events/{id}/evidence")
def get_event_evidence_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    evt = db.query(Event).filter(Event.id == id, Event.tenant_id == tenant_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return {
        "event_id": str(evt.id),
        "evidence": [
            {
                "id": f"EVID_{str(evt.id)[:4].upper()}",
                "type": "IMAGE",
                "file_url": "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=800&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=200&q=80"
            }
        ]
    }

@app.get("/api/v1/evidence/{id}/download")
def download_evidence_v1(id: str, claims: dict = Depends(get_current_user_claims)):
    return {
        "id": id,
        "download_url": "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=800&q=80",
        "mime_type": "image/jpeg"
    }

@app.get("/api/v1/events/{id}/explanation")
def explain_event_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    evt = db.query(Event).filter(Event.id == id, Event.tenant_id == tenant_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")

    from services.vision_service.engines.threat_engine import ExplainableAIEngine
    explanation = ExplainableAIEngine.explain(
        event_type  = getattr(evt, "event_type", "UNKNOWN"),
        risk_score  = float(getattr(evt, "risk_score", 0.0)),
    )

    return {
        "event_id":   str(evt.id),
        "event_type": evt.event_type,
        "risk_score": evt.risk_score,
        "reasons":    explanation["factors"],
        "summary":    explanation["summary"],
        "model":      explanation["model"],
        "privacy_note": explanation["privacy_note"],
    }


# Keep legacy routes for backward compatibility
@app.get("/api/events")
def get_events(status: Optional[str] = None, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return get_events_v1(status, None, None, None, db, claims)

@app.put("/api/events/{event_id}")
def update_event(event_id: str, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    if payload.get("status") == "false_positive":
        return dismiss_event_v1(event_id, db, claims)
    return escalate_event_v1(event_id, db, claims)

@app.get("/api/events/{event_id}/explain")
def explain_event(event_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return explain_event_v1(event_id, db, claims)

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "event_service"}

