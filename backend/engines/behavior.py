import hashlib
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import AnonymousEntity, EntityTrack

class BehaviorIntelligenceEngine:
    @staticmethod
    def analyze_behavior(
        movement_pattern: str,
        zones_visited: list[str],
        objects_detected: list[str],
        dwell_duration_seconds: int
    ) -> dict:
        """
        Creates a behavior signature and details from raw tracking inputs.
        Optimized for behavior tracking instead of people tracking.
        """
        # Generate behavioral signature hash
        raw_sig = f"{movement_pattern}-{','.join(zones_visited)}-{','.join(objects_detected)}-{dwell_duration_seconds}"
        sig_hash = hashlib.sha256(raw_sig.encode()).hexdigest()[:12].upper()
        
        # Calculate velocity indicators
        if "running" in movement_pattern.lower() or "erratic" in movement_pattern.lower():
            movement_profile = "High Velocity / Erratic Path"
        else:
            movement_profile = "Nominal Pace / Standard Path"
            
        zone_profile = " -> ".join(zones_visited)
        
        if objects_detected:
            object_profile = f"Carrying: {', '.join(objects_detected)}"
        else:
            object_profile = "No carried objects detected"
            
        duration_profile = f"{dwell_duration_seconds // 60}m {dwell_duration_seconds % 60}s"
        
        return {
            "behavior_signature": f"SIG-{sig_hash}",
            "movement_profile": movement_profile,
            "zone_profile": zone_profile,
            "object_profile": object_profile,
            "duration_profile": duration_profile
        }

    @staticmethod
    def add_track_point(
        db: Session,
        entity_id: str,
        x: int,
        y: int,
        zone: str,
        speed: float,
        risk_score: float
    ) -> EntityTrack:
        """
        Adds a single movement track point for an anonymous entity.
        This provides breadcrumbs for real-time behavior modeling.
        """
        track = EntityTrack(
            entity_id=entity_id,
            timestamp=datetime.utcnow(),
            location_x=x,
            location_y=y,
            zone=zone,
            speed=speed,
            risk_score=risk_score
        )
        db.add(track)
        
        # Update the parent entity's last seen and last location
        entity = db.query(AnonymousEntity).filter(AnonymousEntity.entity_id == entity_id).first()
        if entity:
            entity.last_seen = datetime.utcnow()
            entity.last_location = zone
            # Update the entity risk score to reflect current trajectory
            entity.risk_score = max(entity.risk_score, risk_score)
            
        db.commit()
        db.refresh(track)
        return track
