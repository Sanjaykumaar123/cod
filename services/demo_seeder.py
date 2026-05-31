import uuid
import random
import datetime
from sqlalchemy.orm import Session
from services.shared.database import SessionLocal, engine, Base
from services.camera_service.infrastructure.models import Camera
from services.vision_service.infrastructure.models import AnonymousEntity, Detection
from services.event_service.infrastructure.models import Event
from services.audit_service.infrastructure.models import AuditLog
from services.identity_governance_service.infrastructure.models import IdentityRequest
from services.auth_service.infrastructure.models import User, Role

def seed_demo_data(tenant_id: str = "default"):
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Camera).filter(Camera.name == "CAM-01 Main Gate").first():
            return {"status": "already seeded"}

        print("Seeding Volume 6 Demo Intelligence Layer...")
        
        # 1. Camera Network
        cameras = [
            ("CAM-01", "Main Gate", "rtsp://192.168.1.101/live", "active", "exterior"),
            ("CAM-02", "Parking Lot", "rtsp://192.168.1.102/live", "active", "exterior"),
            ("CAM-03", "Lobby", "rtsp://192.168.1.103/live", "active", "interior"),
            ("CAM-04", "Elevator", "rtsp://192.168.1.104/live", "active", "interior"),
            ("CAM-05", "Corridor", "rtsp://192.168.1.105/live", "active", "interior"),
            ("CAM-06", "Server Room", "rtsp://192.168.1.106/live", "active", "secure")
        ]
        
        db_cameras = []
        for c_id, name, rtsp, status, zone in cameras:
            cam = Camera(
                name=f"{c_id} {name}",
                rtsp_url=rtsp,
                location=name,
                status=status,
                tenant_id=tenant_id
            )
            db.add(cam)
            db_cameras.append(cam)
        db.commit()
        for cam in db_cameras:
            db.refresh(cam)

        # 2. Anonymous Entities (50 active)
        print("Generating 50 Anonymous Entities...")
        db_entities = []
        zones = ["Main Gate", "Parking Lot", "Lobby", "Elevator", "Corridor", "Server Room"]
        for i in range(50):
            ent_hash = f"ENT-{uuid.uuid4().hex[:4].upper()}"
            cam = random.choice(db_cameras)
            
            risk_score = random.uniform(10.0, 95.0)
            status = "active"
            if risk_score > 85:
                risk_level = "HIGH"
            elif risk_score > 50:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            entity = AnonymousEntity(
                entity_hash=ent_hash,
                camera_id=str(cam.id),
                first_seen=datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(1, 120)),
                last_seen=datetime.datetime.utcnow(),
                risk_score=risk_score,
                status=status,
                tenant_id=tenant_id
            )
            db.add(entity)
            db_entities.append(entity)
        db.commit()

        # 3. Live Events & 4. Explainable AI
        print("Generating Realistic Historical Events...")
        event_types = [
            ("Loitering Detected", 45, "Subject lingered in secure zone for > 300s. Confidence: 0.94"),
            ("Restricted Area Entry", 88, "Entity crossed virtual tripwire into Server Room. Confidence: 0.99"),
            ("Crowd Formation", 65, "Density threshold exceeded in Lobby. Confidence: 0.87"),
            ("Abandoned Object", 92, "Backpack left unattended for 5 minutes. Confidence: 0.96"),
            ("Running Against Flow", 78, "Rapid movement opposite to standard egress vector. Confidence: 0.89"),
            ("Perimeter Breach", 98, "Boundary fence scaled at Sector B. Confidence: 0.97")
        ]

        for i in range(25):
            evt_type, base_risk, explanation = random.choice(event_types)
            cam = random.choice(db_cameras)
            
            event = Event(
                event_type=evt_type,
                severity="HIGH" if base_risk > 80 else "MEDIUM" if base_risk > 50 else "LOW",
                reasoning=f"AI Engine detected {evt_type} at {cam.location}. {explanation}",
                location=cam.location,
                camera_id=str(cam.id),
                risk_score=base_risk + random.uniform(-5, 5),
                tenant_id=tenant_id
            )
            event.created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(1, 300))
            db.add(event)
        db.commit()

        # 6. Audit Logs
        print("Generating Immutable Audit Logs...")
        audit_actions = [
            ("IDENTITY_REQUEST_FILED", "Officer requested Deanonymization for ENT-41B2"),
            ("ENTITY_ANONYMIZED", "Privacy Engine dynamically blurred 45 faces in Frame stream"),
            ("PRIVACY_SHIELD_ACTIVATED", "Global Privacy enforcement enabled on all node edge devices"),
            ("DECRYPTION_REQUEST_REJECTED", "Auditor rejected identity reveal due to insufficient legal cause")
        ]
        
        # Get admin user
        admin = db.query(User).filter(User.username == "admin").first()
        admin_id = str(admin.id) if admin else str(uuid.uuid4())

        for i in range(15):
            action, details = random.choice(audit_actions)
            log = AuditLog(
                user_id=admin_id,
                action=action,
                target_type="System",
                reason=details,
                ip_address=f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
                tenant_id=tenant_id
            )
            db.add(log)
        db.commit()

        # 7. Governance Vault (Identity Requests)
        print("Generating Governance Identity Petitions...")
        statuses = ["pending", "approved_auditor", "approved_admin", "expired"]
        for i in range(10):
            stat = random.choice(statuses)
            req = IdentityRequest(
                requester_id=admin_id,
                entity_id=str(random.choice(db_entities).id),
                justification="Suspicious loitering near restricted asset. Security review required.",
                status=stat,
                tenant_id=tenant_id
            )
            db.add(req)
        db.commit()

        return {"status": "success", "message": "Volume 6 Demo Intelligence Layer successfully seeded."}
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
