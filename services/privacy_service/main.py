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

from services.privacy_service.infrastructure.models import PrivacyScore, ComplianceRule, ExposureRisk

@app.get("/api/v1/privacy/dashboard")
def get_privacy_dashboard_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")

    from services.vision_service.engines.privacy_engine import PrivacyScoreEngine, ComplianceEngine, TrustEngine

    cameras = db.query(Camera).filter(Camera.tenant_id == tenant_id).all()
    shield_count  = sum(1 for c in cameras if c.privacy_shield_active)
    total_cameras = len(cameras) or 1

    # Derive config from camera shield state (approximation when no policy store exists)
    identity_collection = "anonymized_only" if shield_count == total_cameras else "stored_by_default"
    retention_days      = 7  # default governance policy

    priv_result  = PrivacyScoreEngine.calculate(identity_collection=identity_collection, retention_days=retention_days)
    comp_result  = ComplianceEngine.check(identity_collection=identity_collection, retention_days=retention_days)
    trust_score  = TrustEngine.calculate(priv_result["privacy_score"], comp_result["compliance_score"])

    # Store snapshot for history charting
    pm = PrivacyMetric(
        privacy_score       = priv_result["privacy_score"],
        compliance_score    = comp_result["compliance_score"],
        transparency_score  = 97.5,
        retention_risk      = priv_result["risk_level"],
        exposure_risk       = priv_result["risk_level"],
        active_anonymous_count = random.randint(5, 12),
        requests_denied     = 2,
        requests_approved   = 1,
        tenant_id           = tenant_id,
    )
    db.add(pm)
    db.commit()

    return {
        "privacy_score":       priv_result["privacy_score"],
        "risk":                priv_result["risk_level"],
        "compliance_score":    comp_result["compliance_score"],
        "trust_score":         trust_score,
        "transparency_score":  97.5,
        "active_anonymous_count": pm.active_anonymous_count,
        "requests_denied":     2,
        "requests_approved":   1,
        "breakdown":           priv_result["breakdown"],
        "compliance_per_regulation": comp_result["per_regulation"],
    }

@app.post("/api/v1/privacy/assessment")
def run_privacy_assessment_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id   = claims.get("user_id")

    from services.vision_service.engines.privacy_engine import PrivacyScoreEngine, ComplianceEngine, TrustEngine

    cameras = db.query(Camera).filter(Camera.tenant_id == tenant_id).all()
    shield_count  = sum(1 for c in cameras if c.privacy_shield_active)
    total_cameras = len(cameras) or 1

    identity_collection = "anonymized_only" if shield_count == total_cameras else "stored_by_default"
    retention_days      = 7

    priv_result  = PrivacyScoreEngine.calculate(identity_collection=identity_collection, retention_days=retention_days)
    comp_result  = ComplianceEngine.check(identity_collection=identity_collection, retention_days=retention_days)
    trust_score  = TrustEngine.calculate(priv_result["privacy_score"], comp_result["compliance_score"])
    bdown        = priv_result["breakdown"]

    snapshot = PrivacyScore(
        privacy_score            = priv_result["privacy_score"],
        identity_storage_penalty = bdown["identity_penalty"],
        retention_penalty        = bdown["retention_penalty"],
        sharing_penalty          = bdown["sharing_penalty"],
        tracking_penalty         = bdown["tracking_penalty"],
        tenant_id                = tenant_id,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "privacy.assessment", "PrivacyScore", snapshot.id,
                    f"Automated privacy assessment. Score: {priv_result['privacy_score']}")

    recommendations = []
    if identity_collection != "anonymized_only":
        recommendations.append("Switch to anonymized-only mode to gain +25 privacy points.")
    recommendations.append("Enable privacy shield on all camera nodes to maximise anonymization.")
    if comp_result["findings"]:
        recommendations += comp_result["findings"]

    return {
        "assessment_id":       str(snapshot.id),
        "privacy_score":       priv_result["privacy_score"],
        "compliance_score":    comp_result["compliance_score"],
        "trust_score":         trust_score,
        "risk_level":          priv_result["risk_level"],
        "penalties":           bdown,
        "compliance_findings": comp_result["findings"],
        "recommendations":     recommendations,
    }


@app.get("/api/v1/privacy/exposure-risks")
def get_exposure_risks_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    risks = db.query(ExposureRisk).filter(ExposureRisk.tenant_id == tenant_id).all()
    if not risks:
        r1 = ExposureRisk(risk_type="Camera Stream Lack of Anonymization Mask", risk_score=45.0, recommendation="Activate Privacy Shield", tenant_id=tenant_id)
        r2 = ExposureRisk(risk_type="Long Retention Period of Raw Movement Coordinates", risk_score=15.0, recommendation="Shorten retention limit to 7 days", tenant_id=tenant_id)
        db.add_all([r1, r2])
        db.commit()
        risks = [r1, r2]
    return risks

@app.get("/api/v1/privacy/compliance")
def get_compliance_rules_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    rules = db.query(ComplianceRule).filter(ComplianceRule.tenant_id == tenant_id).all()
    if not rules:
        r1 = ComplianceRule(rule_name="GDPR Article 35 - DPIA Requirement", description="Data Protection Impact Assessment must be run routinely on automated surveillance.", severity="high", tenant_id=tenant_id)
        r2 = ComplianceRule(rule_name="CCPA Section 1798.100 - Access Notice", description="Notify visitors at physical entryways regarding facial blurring protection.", severity="medium", tenant_id=tenant_id)
        db.add_all([r1, r2])
        db.commit()
        rules = [r1, r2]
    return rules

# Keep legacy route for compatibility
@app.get("/api/privacy-metrics")
def get_privacy_metrics(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    history = db.query(PrivacyMetric).filter(PrivacyMetric.tenant_id == tenant_id).order_by(PrivacyMetric.id.desc()).limit(10).all()
    history_reversed = list(reversed(history))
    
    return {
        "current": {
            "privacy_score": 94.2,
            "compliance_score": 96.0,
            "transparency_score": 97.5,
            "retention_risk": "Low",
            "exposure_risk": "Low",
            "active_anonymous_count": 8,
            "requests_denied": 2,
            "requests_approved": 1
        },
        "history": [
            {
                "timestamp": h.created_at.strftime("%H:%M") if h.created_at else datetime.now().strftime("%H:%M"),
                "privacy_score": h.privacy_score,
                "compliance_score": h.compliance_score,
                "transparency_score": h.transparency_score,
                "active_anonymous_count": h.active_anonymous_count
            }
            for h in history_reversed
        ],
        "recommendations": [
            "Purge metadata logs older than 7 days (GDPR compliance optimization).",
            "Enable double-blind authorization locks on Gate Alpha video nodes."
        ]
    }

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "privacy_service"}

