import hashlib
import random
import uuid
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import AnonymousEntity, PrivacyMetric

class PrivacyEngine:
    @staticmethod
    def generate_anonymous_id() -> str:
        """
        Generates a privacy-compliant identifier like Entity_93A7.
        This represents the anonymized handle for a specific individual.
        """
        # Create a unique 4-character hex suffix
        unique_suffix = uuid.uuid4().hex[:4].upper()
        return f"Entity_{unique_suffix}"

    @staticmethod
    def anonymize_face_metadata(raw_face_image_bytes: bytes) -> str:
        """
        Simulates destroying the original face. We convert it to a SHA-256 signature
        and discard the raw image bytes. In a real system, this happens in-memory
        and the original pixels are never written to disk.
        """
        hasher = hashlib.sha256()
        hasher.update(raw_face_image_bytes)
        return hasher.hexdigest()

    @staticmethod
    def create_entity(
        db: Session,
        last_location: str,
        risk_score: float = 0.0,
        behavior_sig: str = None,
        mov_prof: str = None,
        zone_prof: str = None,
        obj_prof: str = None,
        dur_prof: str = None
    ) -> AnonymousEntity:
        """
        Registers an anonymized entity in the system, preserving behavior but destroying identity.
        """
        entity_id = PrivacyEngine.generate_anonymous_id()
        entity = AnonymousEntity(
            entity_id=entity_id,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            last_location=last_location,
            risk_score=risk_score,
            behavior_signature=behavior_sig or hashlib.md5(entity_id.encode()).hexdigest()[:8].upper(),
            movement_profile=mov_prof or "Standard velocity, normal gait",
            zone_profile=zone_prof or f"Public Lobby -> {last_location}",
            object_profile=obj_prof or "No prohibited items",
            duration_profile=dur_prof or "0m (active)",
            status="active"
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def calculate_privacy_metrics(db: Session) -> dict:
        """
        Computes the live Privacy Score, Exposure Risk, and Retention Risk.
        Privacy Score decreases if identity collection is enabled or if too many
        active decryptions/requests exist.
        """
        active_entities = db.query(AnonymousEntity).filter(AnonymousEntity.status == "active").count()
        
        # In a real system, count the active decryption leases
        from backend.models import IdentityRequest
        approved_requests = db.query(IdentityRequest).filter(
            IdentityRequest.status == "approved"
        ).count()
        
        # Calculate Scores
        privacy_score = max(100.0 - (approved_requests * 15.0), 40.0)
        compliance_score = 98.5 if approved_requests == 0 else max(98.5 - (approved_requests * 5.0), 75.0)
        transparency_score = 100.0 - (approved_requests * 2.0)
        
        retention_risk = "Low" if active_entities < 50 else ("Medium" if active_entities < 100 else "High")
        exposure_risk = "Low" if approved_requests == 0 else ("Medium" if approved_requests <= 2 else "High")
        
        # Create and save a new metric point
        metric = PrivacyMetric(
            timestamp=datetime.utcnow(),
            privacy_score=privacy_score,
            compliance_score=compliance_score,
            transparency_score=transparency_score,
            retention_risk=retention_risk,
            exposure_risk=exposure_risk,
            active_anonymous_count=active_entities,
            requests_denied=0, # updated dynamically
            requests_approved=approved_requests
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return {
            "privacy_score": privacy_score,
            "compliance_score": compliance_score,
            "transparency_score": transparency_score,
            "retention_risk": retention_risk,
            "exposure_risk": exposure_risk,
            "active_anonymous_count": active_entities
        }
