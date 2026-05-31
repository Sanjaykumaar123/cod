"""
BlindWatch Simulator Service  –  v2.0 (Volume 5)
================================================
Uses the full SimulatorEngine with Volume-5 formulas:
  - safety_score  = camera_coverage*0.3 + threat_detection*0.4 + response_speed*0.3
  - fpr           = sensitivity * crowd_density_factor
  - bias_risk     = tracking_intensity * identity_collection_factor
  - trust_score   = privacy*0.5 + compliance*0.3 + transparency*0.2
"""
import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel

from services.shared.database import get_db, SessionLocal
from services.simulator_service.infrastructure.models import SimulationResult

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM  = "HS256"

app = FastAPI(title="BlindWatch Simulator Service", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token claims")


class SimulationRequest(BaseModel):
    config_name: str = "Policy Simulation"
    cameras_count: int = 12
    retention_days: int = 7
    sensitivity: float = 0.75
    identity_collection: str = "anonymized_only"   # anonymized_only | stored_by_default | raw_biometric
    crowd_density: str = "medium"                   # low | medium | high
    threat_level: str = "medium"                    # low | medium | high


@app.post("/api/v1/simulator/run")
@app.post("/api/v1/simulator")
@app.post("/api/simulator")
def run_simulation(req: SimulationRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")

    # Run the full engine
    from services.vision_service.engines.simulator_engine import SimulatorEngine
    result = SimulatorEngine.run(
        cameras_count       = req.cameras_count,
        retention_days      = req.retention_days,
        sensitivity         = req.sensitivity,
        identity_collection = req.identity_collection,
        crowd_density       = req.crowd_density,
        threat_level        = req.threat_level,
        config_name         = req.config_name,
    )

    bw = result["blindwatch"]
    tr = result["traditional"]

    # Persist to DB
    sim_record = SimulationResult(
        config_name              = req.config_name,
        cameras_count            = req.cameras_count,
        retention_days           = req.retention_days,
        sensitivity              = req.sensitivity,
        identity_collection      = req.identity_collection,
        crowd_density            = req.crowd_density,
        threat_level             = req.threat_level,
        traditional_safety_score = tr["safety_score"],
        blindwatch_safety_score  = bw["safety_score"],
        traditional_privacy_score= tr["privacy_score"],
        blindwatch_privacy_score = bw["privacy_score"],
        recommendations          = "; ".join(result["recommendations"]),
        tenant_id                = tenant_id,
    )
    db.add(sim_record)
    db.commit()
    db.refresh(sim_record)

    # Return full rich result to UI
    return {
        "simulation_id":  str(sim_record.id),
        "config_name":    req.config_name,
        "blindwatch":     bw,
        "traditional":    tr,
        "inputs":         result["inputs"],
        "recommendations": result["recommendations"],
        "compliance_findings": result.get("compliance_findings", []),
    }


@app.get("/api/v1/simulator/results")
@app.get("/api/simulator/results")
def get_simulator_results(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    rows = db.query(SimulationResult).filter(SimulationResult.tenant_id == tenant_id).order_by(SimulationResult.id.desc()).all()
    return rows


@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "simulator_service", "version": "2.0.0"}
