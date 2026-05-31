import os
import random
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from jose import jwt, JWTError

from services.shared.database import get_db, Base, engine, SessionLocal, TenantMixin
from services.camera_service.infrastructure.models import Camera

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

from services.privacy_service.infrastructure.models import PrivacyMetric

app = FastAPI(title="BlindWatch Privacy Service", version="1.0.0")

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
def seed_privacy_metrics():

    db = SessionLocal()
    try:
        if not db.query(PrivacyMetric).first():
            print("Seeding privacy history points in modular db...")
            for i in range(10):
                pm = PrivacyMetric(
                    privacy_score=95.0 + random.uniform(-2, 3),
                    compliance_score=98.0 + random.uniform(-1, 1),
                    transparency_score=97.0 + random.uniform(-1, 2),
                    retention_risk="Low",
                    exposure_risk="Low",
                    active_anonymous_count=random.randint(5, 15),
                    requests_denied=0,
                    requests_approved=0,
                    tenant_id="default"
                )
                db.add(pm)
            db.commit()
            print("Seeded privacy history.")
    finally:
        db.close()

@app.get("/api/privacy-metrics")
def get_privacy_metrics(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    
    # Calculate dynamic metrics based on active cameras privacy shield state
    cameras = db.query(Camera).filter(Camera.tenant_id == tenant_id).all()
    shield_count = sum(1 for c in cameras if c.privacy_shield_active)
    total_cameras = len(cameras) or 1
    
    # Base safety metrics
    base_privacy = 70.0 + (shield_count / total_cameras) * 30.0
    base_compliance = 90.0 + (shield_count / total_cameras) * 10.0
    
    current_metrics = {
        "id": 1,
        "privacy_score": round(base_privacy, 1),
        "compliance_score": round(base_compliance, 1),
        "transparency_score": 97.5,
        "retention_risk": "Low" if base_privacy > 85 else "Medium",
        "exposure_risk": "Low" if base_privacy > 90 else "Medium",
        "active_anonymous_count": random.randint(5, 12),
        "requests_denied": 2,
        "requests_approved": 1
    }
    
    # Record dynamic point
    history_point = PrivacyMetric(
        privacy_score=current_metrics["privacy_score"],
        compliance_score=current_metrics["compliance_score"],
        transparency_score=current_metrics["transparency_score"],
        retention_risk=current_metrics["retention_risk"],
        exposure_risk=current_metrics["exposure_risk"],
        active_anonymous_count=current_metrics["active_anonymous_count"],
        requests_denied=current_metrics["requests_denied"],
        requests_approved=current_metrics["requests_approved"],
        tenant_id=tenant_id
    )
    db.add(history_point)
    db.commit()
    
    # Fetch historical points
    history = db.query(PrivacyMetric).filter(PrivacyMetric.tenant_id == tenant_id).order_by(PrivacyMetric.id.desc()).limit(10).all()
    history_reversed = list(reversed(history))
    
    return {
        "current": current_metrics,
        "history": [
            {
                "timestamp": h.created_at.strftime("%H:%M") if hasattr(h, "created_at") and h.created_at else datetime.now().strftime("%H:%M"),
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
