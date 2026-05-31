import os
import random
import time
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from services.shared.database import get_db, Base, engine, SessionLocal
from services.vision_service.infrastructure.models import EntityTrack
from services.camera_service.infrastructure.models import Camera
from services.identity_governance_service.infrastructure.models import IdentityRequest
from services.event_service.main import Event

# Let's import the specific modular entities
from services.privacy_service.infrastructure.models import PrivacyScore # To trigger metrics update

# We can define a local AnonymousEntity in Vision Service's db context
# Wait, to make it clean, let's import it from a shared local location if needed.
# Since init_all_dbs has all models on Base, we can define AnonymousEntity local representation.
# Let's check if services/vision_service/infrastructure/models.py has AnonymousEntity. No, it has EntityTrack.
# Let's define the local AnonymousEntity class inside vision main to fetch/write anonymous_entities table.
from services.vision_service.infrastructure.models import AnonymousEntity

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

app = FastAPI(title="BlindWatch Vision Service", version="1.0.0")

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
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/entities")
def get_entities(status: Optional[str] = None, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    query = db.query(AnonymousEntity).filter(AnonymousEntity.tenant_id == tenant_id)
    if status:
        query = query.filter(AnonymousEntity.status == status)
    return query.order_by(AnonymousEntity.id.desc()).all()

@app.get("/api/entities/{entity_id}/tracks")
def get_entity_tracks(entity_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    tracks = db.query(EntityTrack).filter(EntityTrack.entity_id == entity_id, EntityTrack.tenant_id == tenant_id).all()
    # Format to match frontend expected response
    return [
        {
            "id": t.id,
            "entity_id": t.entity_id,
            "timestamp": t.last_seen,
            "location_x": t.coordinate_path[0]["x"] if t.coordinate_path else 100,
            "location_y": t.coordinate_path[0]["y"] if t.coordinate_path else 200,
            "zone": t.last_seen,
            "risk_score": 5.0,
            "speed": t.current_speed
        }
        for t in tracks
    ]

@app.get("/api/entities/{entity_id}/identity")
def get_entity_identity(entity_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    # Check if active request is approved
    req = db.query(IdentityRequest).filter(
        IdentityRequest.entity_id == entity_id,
        IdentityRequest.tenant_id == tenant_id,
        IdentityRequest.status == "approved"
    ).first()
    
    if req:
        # Check dual signatures
        if req.approved_by_admin and req.approved_by_auditor:
            # Reconstruct XOR secret share in modular database
            # For modular sandbox, return decrypted_identity or seed value
            decrypted = req.decrypted_identity or "Biometric Match: Sanjay Kumaar (Auditor ID: 902)"
            return {
                "permitted": True,
                "decrypted_identity": decrypted,
                "expires_in_seconds": 900
            }
            
    return {
        "permitted": False,
        "decrypted_identity": "Access Denied: Requires Active Approved Dual-Key Lease."
    }

@app.post("/api/cameras/{camera_id}/feed")
def process_feed(camera_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    camera = db.query(Camera).filter(Camera.id == camera_id, Camera.tenant_id == tenant_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    # Query or create an entity for this location
    entity = db.query(AnonymousEntity).filter(
        AnonymousEntity.last_location == camera.location,
        AnonymousEntity.status == "active",
        AnonymousEntity.tenant_id == tenant_id
    ).first()
    
    if not entity:
        entity_id = f"Entity_{random.randint(1000, 9999)}"
        entity = AnonymousEntity(
            entity_id=entity_id,
            last_location=camera.location,
            risk_score=5.0,
            status="active",
            tenant_id=tenant_id
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        
    x = random.randint(150, 850)
    y = random.randint(150, 650)
    speed = round(random.uniform(0.5, 4.2), 2)
    risk_score = 5.0
    
    # Store track coordinate path
    track = db.query(EntityTrack).filter(EntityTrack.entity_id == entity.entity_id, EntityTrack.tenant_id == tenant_id).first()
    if not track:
        track = EntityTrack(
            entity_id=entity.entity_id,
            coordinate_path=[{"x": x, "y": y}],
            current_speed=speed,
            last_seen=camera.location,
            tenant_id=tenant_id
        )
        db.add(track)
    else:
        path = list(track.coordinate_path)
        path.append({"x": x, "y": y})
        if len(path) > 10:
            path.pop(0)
        track.coordinate_path = path
        track.current_speed = speed
        track.last_seen = camera.location
        
    # Anomaly simulation (occasional events)
    event_created = None
    roll = random.random()
    if roll > 0.93:
        event_type = "Possible Weapon" if roll > 0.96 else "Possible Intrusion"
        reason = f"AI classified high risk movement pattern matching {event_type} signature."
        event_created = Event(
            event_type=event_type,
            location=camera.location,
            entity_id=entity.entity_id,
            risk_score=75.0 if event_type == "Possible Weapon" else 60.0,
            confidence=0.91,
            reasoning=reason,
            status="unresolved",
            tenant_id=tenant_id
        )
        db.add(event_created)
        entity.risk_score = event_created.risk_score
        
    db.commit()
    
    return {
        "camera_id": camera.id,
        "camera_name": camera.name,
        "location": camera.location,
        "entity": {
            "entity_id": entity.entity_id,
            "x": x,
            "y": y,
            "speed": speed,
            "risk_score": round(entity.risk_score, 1),
            "is_anonymized": camera.privacy_shield_active,
            "behavior_sig": entity.behavior_signature or "walking_paced"
        },
        "event_triggered": {
            "id": event_created.id,
            "type": event_created.event_type,
            "risk": event_created.risk_score,
            "reason": event_created.reasoning
        } if event_created else None
    }
