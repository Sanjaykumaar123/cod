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

# Map SimulationResult to table 'simulation_results' in the modular db
class SimulationResult(Base, TenantMixin):
    __tablename__ = 'simulation_results'
    
    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(100), nullable=False)
    cameras_count = Column(Integer, nullable=False)
    retention_days = Column(Integer, nullable=False)
    sensitivity = Column(Float, nullable=False)
    identity_collection = Column(String(100), nullable=False)
    crowd_density = Column(String(50), nullable=False)
    threat_level = Column(String(50), nullable=False)
    
    traditional_safety_score = Column(Float, default=70.0)
    blindwatch_safety_score = Column(Float, default=95.0)
    traditional_privacy_score = Column(Float, default=20.0)
    blindwatch_privacy_score = Column(Float, default=98.0)
    recommendations = Column(String(1000), nullable=True)

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

app = FastAPI(title="BlindWatch Simulator Service", version="1.0.0")

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



@app.post("/api/simulator")
def run_simulation(payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    
    cams = payload.get("cameras_count", 12)
    sens = payload.get("sensitivity", 0.75)
    threat = payload.get("threat_level", "medium")
    
    # Calculate comparative metrics
    trad_safety = 50.0 + (cams * 1.5) + (sens * 10)
    bw_safety = trad_safety - 2.0  # slight drop because of privacy-guard delay
    
    trad_privacy = 15.0 if payload.get("identity_collection") == "raw_biometric" else 35.0
    bw_privacy = 98.0 - (cams * 0.1)
    
    rec = "Verify that retention constraints align with regional directives. Enable double-key access rules on sensitive zones."
    
    res = SimulationResult(
        config_name=payload.get("config_name", "Local Area Test"),
        cameras_count=cams,
        retention_days=payload.get("retention_days", 14),
        sensitivity=sens,
        identity_collection=payload.get("identity_collection", "default_anonymized"),
        crowd_density=payload.get("crowd_density", "medium"),
        threat_level=threat,
        traditional_safety_score=round(min(trad_safety, 99.0), 1),
        blindwatch_safety_score=round(min(bw_safety, 98.0), 1),
        traditional_privacy_score=round(trad_privacy, 1),
        blindwatch_privacy_score=round(bw_privacy, 1),
        recommendations=rec,
        tenant_id=tenant_id
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

@app.get("/api/simulator/results")
def get_simulator_results(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    return db.query(SimulationResult).filter(SimulationResult.tenant_id == tenant_id).order_by(SimulationResult.id.desc()).all()
