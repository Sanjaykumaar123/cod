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

import asyncio
from fastapi import WebSocket, WebSocketDisconnect

@app.get("/api/v1/entities")
def get_entities_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    entities = db.query(AnonymousEntity).filter(AnonymousEntity.tenant_id == tenant_id).all()
    return [
        {
            "id": str(ent.id),
            "entity_id": ent.entity_id or f"ENT_{str(ent.id)[:4].upper()}",
            "risk_score": ent.risk_score,
            "status": ent.status,
            "last_location": ent.last_location,
            "behavior_signature": ent.behavior_signature or "normal_gait"
        }
        for ent in entities
    ]

@app.get("/api/v1/entities/{id}")
def get_entity_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    # Search by UUID or custom entity_id string
    ent = db.query(AnonymousEntity).filter(
        (AnonymousEntity.id == id) | (AnonymousEntity.entity_id == id),
        AnonymousEntity.tenant_id == tenant_id
    ).first()
    
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    tracks = db.query(EntityTrack).filter(EntityTrack.entity_id == ent.entity_id, EntityTrack.tenant_id == tenant_id).all()
    movement_history = []
    for t in tracks:
        movement_history.append({
            "timestamp": str(t.updated_at),
            "location": t.last_seen,
            "coordinates": t.coordinate_path,
            "speed": t.current_speed
        })
        
    return {
        "id": str(ent.id),
        "entity_id": ent.entity_id,
        "risk_score": ent.risk_score,
        "behavior_profile": {
            "signature": ent.behavior_signature or "normal_walking",
            "pace": "standard",
            "risk_class": "low" if ent.risk_score < 40 else ("medium" if ent.risk_score < 75 else "high")
        },
        "movement_history": movement_history,
        "risk_history": [
            {"timestamp": str(ent.created_at), "score": ent.risk_score}
        ]
    }

@app.get("/api/v1/live-feed/{camera_id}")
def get_live_feed_v1(camera_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    return {
        "camera_id": camera_id,
        "frame": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "entities": [
            {"entity_id": "ENT_8842", "bbox": [100, 150, 80, 200], "risk_score": 12.0}
        ]
    }

@app.websocket("/ws/live-feed/{camera_id}")
async def ws_live_feed_v1(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "frame": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "entities": [
                    {
                        "entity_id": "ENT_A93F",
                        "x": random.randint(100, 800),
                        "y": random.randint(100, 600),
                        "risk_score": random.randint(10, 80)
                    }
                ]
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# Keep local processing route for compatibility
@app.post("/api/cameras/{camera_id}/feed")
def process_feed(camera_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    camera = db.query(Camera).filter(Camera.id == camera_id, Camera.tenant_id == tenant_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    entity = db.query(AnonymousEntity).filter(
        AnonymousEntity.last_location == camera.location,
        AnonymousEntity.status == "active",
        AnonymousEntity.tenant_id == tenant_id
    ).first()
    
    if not entity:
        entity_id_str = f"Entity_{random.randint(1000, 9999)}"
        entity = AnonymousEntity(
            entity_id=entity_id_str,
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
            "id": str(event_created.id),
            "type": event_created.event_type,
            "risk": event_created.risk_score,
            "reason": event_created.reasoning
        } if event_created else None
    }

@app.get("/api/entities/{entity_id}/tracks")
def get_entity_tracks_compat(entity_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return get_entity_tracks(entity_id, db, claims)

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "vision_service"}


