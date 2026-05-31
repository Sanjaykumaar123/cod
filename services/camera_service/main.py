import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from services.shared.database import get_db, Base, engine, SessionLocal
from services.camera_service.infrastructure.models import Camera, CameraStatus

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

app = FastAPI(title="BlindWatch Camera Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
        
    def __call__(self, claims: dict = Depends(get_current_user_claims)) -> dict:
        if claims.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation denied. Requires: {self.allowed_roles}"
            )
        return claims

@app.on_event("startup")
def startup_seed_cameras():

    db = SessionLocal()
    try:
        if not db.query(Camera).first():
            print("Seeding cameras in modular db...")
            default_cameras = [
                ("North Gate Entrance", "Entrance", "rtsp://192.168.1.100/stream1"),
                ("Main Lobby Desk", "Lobby", "rtsp://192.168.1.101/stream1"),
                ("South Perimeter Fence", "Perimeter", "rtsp://192.168.1.102/stream1"),
                ("West Corridor Hallway", "Corridor", "rtsp://192.168.1.103/stream1"),
                ("Restricted Vault Room", "Restricted Zone", "rtsp://192.168.1.104/stream1")
            ]
            
            for name, loc, rtsp in default_cameras:
                cam = Camera(
                    name=name,
                    location=loc,
                    rtsp_url=rtsp,
                    resolution="1920x1080",
                    fps=30,
                    is_active=True,
                    privacy_shield_active=True,
                    safety_score=95.0,
                    tenant_id="default"
                )
                db.add(cam)
                db.commit()
                db.refresh(cam)
                
                # Create initial health status log
                status_log = CameraStatus(
                    camera_id=cam.id,
                    status="active",
                    latency_ms=12.5,
                    tenant_id="default"
                )
                db.add(status_log)
                db.commit()
            print("Modular cameras seeded.")
    finally:
        db.close()

@app.get("/api/cameras")
def get_cameras(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    cameras = db.query(Camera).filter(Camera.tenant_id == tenant_id).all()
    # Format to match frontend schema
    return [
        {
            "id": cam.id,
            "name": cam.name,
            "rtsp_url": cam.rtsp_url,
            "location": cam.location,
            "status": "active" if cam.is_active else "offline",
            "resolution": cam.resolution,
            "fps": cam.fps,
            "is_active": cam.is_active,
            "privacy_shield_active": cam.privacy_shield_active,
            "safety_score": cam.safety_score,
            "threat_count": 0 # updated via vision
        }
        for cam in cameras
    ]

@app.post("/api/cameras")
def create_camera(payload: dict, db: Session = Depends(get_db), claims: dict = Depends(RoleChecker(["admin", "officer"]))):
    tenant_id = claims.get("tenant_id", "default")
    cam = Camera(
        name=payload.get("name"),
        location=payload.get("location"),
        rtsp_url=payload.get("rtsp_url", "rtsp://127.0.0.1/live"),
        resolution=payload.get("resolution", "1080p"),
        fps=payload.get("fps", 30),
        is_active=True,
        privacy_shield_active=payload.get("privacy_shield_active", True),
        safety_score=100.0,
        tenant_id=tenant_id
    )
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam

@app.put("/api/cameras/{camera_id}/privacy-shield")
def toggle_privacy_shield(camera_id: int, active: bool, db: Session = Depends(get_db), claims: dict = Depends(RoleChecker(["admin", "officer", "auditor"]))):
    tenant_id = claims.get("tenant_id", "default")
    cam = db.query(Camera).filter(Camera.id == camera_id, Camera.tenant_id == tenant_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.privacy_shield_active = active
    db.commit()
    db.refresh(cam)
    return {"status": "success", "camera_id": cam.id, "privacy_shield_active": cam.privacy_shield_active}
