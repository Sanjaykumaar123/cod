import datetime
from backend.database import Base, engine, SessionLocal
from backend.models import User, Camera, AnonymousEntity, EntityTrack, Event, PrivacyMetric, AuditLog, IdentityRequest
from backend.auth import get_password_hash

def seed_db():
    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding database...")
        
        # 1. Users
        users = [
            User(
                username="admin",
                email="admin@blindwatch.ai",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                full_name="Alex Mercer (System Administrator)",
                is_active=True
            ),
            User(
                username="auditor",
                email="auditor@blindwatch.ai",
                hashed_password=get_password_hash("auditor123"),
                role="auditor",
                full_name="Sarah Vance (Compliance Auditor)",
                is_active=True
            ),
            User(
                username="officer",
                email="officer@blindwatch.ai",
                hashed_password=get_password_hash("officer123"),
                role="officer",
                full_name="Marcus Briggs (Security Lead)",
                is_active=True
            ),
            User(
                username="viewer",
                email="viewer@blindwatch.ai",
                hashed_password=get_password_hash("viewer123"),
                role="viewer",
                full_name="Dana Scully (Operations Operator)",
                is_active=True
            )
        ]
        db.add_all(users)
        db.commit()
        
        # 2. Cameras
        cameras = [
            Camera(name="CAM-01-LOBBY", location="Main Lobby", rtsp_url="rtsp://192.168.1.50/stream1", status="active", safety_score=94.5, threat_count=1),
            Camera(name="CAM-02-PERIMETER", location="North Perimeter", rtsp_url="rtsp://192.168.1.51/stream1", status="active", safety_score=85.0, threat_count=2),
            Camera(name="CAM-03-SERVER", location="Server Room C", rtsp_url="rtsp://192.168.1.52/stream1", status="active", safety_score=99.0, threat_count=0),
            Camera(name="CAM-04-GATE", location="Gate Alpha", rtsp_url="rtsp://192.168.1.53/stream1", status="active", safety_score=78.2, threat_count=3),
            Camera(name="CAM-05-DOCK", location="Loading Dock", rtsp_url="rtsp://192.168.1.54/stream1", status="offline", safety_score=95.0, threat_count=0)
        ]
        db.add_all(cameras)
        db.commit()
        
        # 3. Anonymous Entities
        entities = [
            AnonymousEntity(
                entity_id="Entity_93A7",
                first_seen=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
                last_seen=datetime.datetime.utcnow(),
                last_location="Main Lobby",
                risk_score=15.0,
                behavior_signature="SIG-892F1A9BC",
                movement_profile="Paced walking speed. Regular stride.",
                zone_profile="Parking Lot -> Main Lobby",
                object_profile="Carrying: Briefcase",
                duration_profile="120m (active)",
                status="active"
            ),
            AnonymousEntity(
                entity_id="Entity_2B8C",
                first_seen=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
                last_seen=datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
                last_location="Gate Alpha",
                risk_score=82.5,
                behavior_signature="SIG-119D8EFA3",
                movement_profile="Erratic jogging. Sudden changes in vector directions.",
                zone_profile="Gate Alpha -> Fence Sector 3 -> Gate Alpha",
                object_profile="Carrying: Metallic Item (Prohibited)",
                duration_profile="50m (departed)",
                status="departed"
            ),
            AnonymousEntity(
                entity_id="Entity_F15E",
                first_seen=datetime.datetime.utcnow() - datetime.timedelta(minutes=45),
                last_seen=datetime.datetime.utcnow(),
                last_location="Server Room C",
                risk_score=48.0,
                behavior_signature="SIG-BB2C70E91",
                movement_profile="Slow stealth-like step. Lingering near entryways.",
                zone_profile="North Corridor -> Server Room C Entry",
                object_profile="Carrying: Mobile Device",
                duration_profile="45m (active)",
                status="active"
            ),
            AnonymousEntity(
                entity_id="Entity_E55A",
                first_seen=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                last_seen=datetime.datetime.utcnow() - datetime.timedelta(minutes=5),
                last_location="Loading Dock",
                risk_score=10.0,
                behavior_signature="SIG-33A899C12",
                movement_profile="Steady walking.",
                zone_profile="Loading Dock Exterior",
                object_profile="Carrying: Cardboard Box",
                duration_profile="25m (departed)",
                status="departed"
            )
        ]
        db.add_all(entities)
        db.commit()
        
        # 4. Tracks
        tracks = [
            EntityTrack(entity_id="Entity_93A7", location_x=340, location_y=420, zone="Parking Lot", speed=1.2, risk_score=5.0),
            EntityTrack(entity_id="Entity_93A7", location_x=450, location_y=380, zone="Main Lobby", speed=1.1, risk_score=10.0),
            EntityTrack(entity_id="Entity_93A7", location_x=510, location_y=400, zone="Main Lobby", speed=0.8, risk_score=15.0),
            
            EntityTrack(entity_id="Entity_2B8C", location_x=700, location_y=150, zone="Gate Alpha", speed=2.5, risk_score=30.0),
            EntityTrack(entity_id="Entity_2B8C", location_x=720, location_y=120, zone="Fence Sector 3", speed=4.5, risk_score=65.0),
            EntityTrack(entity_id="Entity_2B8C", location_x=710, location_y=140, zone="Gate Alpha", speed=3.8, risk_score=82.5),
            
            EntityTrack(entity_id="Entity_F15E", location_x=210, location_y=550, zone="North Corridor", speed=0.9, risk_score=20.0),
            EntityTrack(entity_id="Entity_F15E", location_x=225, location_y=580, zone="Server Room C Entry", speed=0.4, risk_score=48.0)
        ]
        db.add_all(tracks)
        db.commit()
        
        # 5. Events
        # Let's seed two events
        event1 = Event(
            event_type="Possible Weapon",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=12),
            location="Gate Alpha",
            entity_id="Entity_2B8C",
            risk_score=82.5,
            confidence=0.88,
            evidence_image="weapon_box_alpha",
            reasoning='{"summary": "Detected high-probability Possible Weapon at Gate Alpha.", "confidence": "88.0%", "factors": {"Weapon Detection (Type: Lethal Threat)": 75.0, "Movement Anomaly (Sudden Velocity Spike)": 20.0}}',
            timeline='[{"time": "22:02:15", "log": "Entity_2B8C tracked entering perimeter Gate Alpha."}, {"time": "22:05:40", "log": "Object classifier identified high-contrast metallic tool (pistol outline)."}, {"time": "22:07:01", "log": "Alert emitted to command console."}]',
            status="unresolved",
            is_false_positive=False
        )
        
        event2 = Event(
            event_type="Possible Intrusion",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=35),
            location="Server Room C",
            entity_id="Entity_F15E",
            risk_score=48.0,
            confidence=0.91,
            evidence_image="intrusion_box_server",
            reasoning='{"summary": "Detected high-probability Possible Intrusion at Server Room C.", "confidence": "91.0%", "factors": {"Unauthorized Access (Restricted Area)": 35.0, "Movement Anomaly (Dwell/Lingering)": 15.0}}',
            timeline='[{"time": "21:39:10", "log": "Entity_F15E entered Server Room C secure hallway."}, {"time": "21:41:05", "log": "Biometric door lock failure registered concurrent with proximity."}, {"time": "21:44:00", "log": "Console alerted Security Officer Briggs."}]',
            status="unresolved",
            is_false_positive=False
        )
        db.add(event1)
        db.add(event2)
        db.commit()
        
        # 6. Privacy Metrics
        metrics = [
            PrivacyMetric(
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=4),
                privacy_score=100.0,
                compliance_score=100.0,
                transparency_score=100.0,
                retention_risk="Low",
                exposure_risk="Low",
                active_anonymous_count=2,
                requests_denied=0,
                requests_approved=0
            ),
            PrivacyMetric(
                timestamp=datetime.datetime.utcnow(),
                privacy_score=97.5,
                compliance_score=99.0,
                transparency_score=98.8,
                retention_risk="Low",
                exposure_risk="Low",
                active_anonymous_count=4,
                requests_denied=1,
                requests_approved=0
            )
        ]
        db.add_all(metrics)
        db.commit()
        
        # 7. Identity Requests
        req1 = IdentityRequest(
            requester_id=3, # Marcus Briggs (officer)
            requester_name="Marcus Briggs",
            entity_id="Entity_93A7",
            justification="Subject seen lingering near treasury lockbox. Need to verify clearing staff credentials.",
            status="pending",
            duration_minutes=30,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=15),
            approved_by_auditor=False,
            approved_by_admin=False
        )
        req2 = IdentityRequest(
            requester_id=3,
            requester_name="Marcus Briggs",
            entity_id="Entity_2B8C",
            justification="Weapon alert triggered in perimeter area. Law enforcement request for immediate identity release.",
            status="approved",
            duration_minutes=30,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=5),
            approved_by_auditor=True,
            approved_by_admin=True,
            approved_by_auditor_name="Sarah Vance",
            approved_by_admin_name="Alex Mercer",
            approved_by_auditor_id=2,
            approved_by_admin_id=1,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=25),
            decrypted_identity="Sarah M. Jenkins (ID: 9812A) - SmartCard Registered Staff"
        )
        db.add(req1)
        db.add(req2)
        db.commit()
        
        # 8. Audit Logs
        logs = [
            AuditLog(user_id=1, username="admin", role="admin", action="SYSTEM_INIT", reason="Database initialized and default schema verified.", outcome="success"),
            AuditLog(user_id=3, username="officer", role="officer", action="IDENTITY_DECRYPTION_REQUEST", reason="Submitted ID request for Entity_93A7.", outcome="success"),
            AuditLog(user_id=3, username="officer", role="officer", action="IDENTITY_DECRYPTION_REQUEST", reason="Submitted ID request for Entity_2B8C.", outcome="success"),
            AuditLog(user_id=2, username="auditor", role="auditor", action="IDENTITY_DECRYPTION_AUDITOR_APPROVE", reason="Auditor approved request for Entity_2B8C due to lethal threat flag.", outcome="success"),
            AuditLog(user_id=1, username="admin", role="admin", action="IDENTITY_DECRYPTION_ADMIN_APPROVE", reason="Admin approved request for Entity_2B8C, granting temporary decrypt lease.", outcome="success")
        ]
        db.add_all(logs)
        db.commit()
        
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
