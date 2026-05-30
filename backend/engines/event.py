import json
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import Event, AnonymousEntity, Camera
from backend.engines.risk import RiskScoringEngine

class EventEngine:
    @staticmethod
    def create_event(
        db: Session,
        event_type: str, # Possible Theft, Possible Violence, Possible Weapon, Possible Intrusion, Fire Hazard, Crowd Panic, Medical Emergency
        location: str,
        entity_id: str,
        risk_score: float,
        confidence: float,
        evidence_image: str = None,
        raw_factors: dict = None
    ) -> Event:
        """
        Creates a structured safety event and attaches Explainable AI logic.
        """
        # Formulate reasoning explanation based on contributing factors
        reasoning_dict = {
            "summary": f"Detected high-probability {event_type} at {location}.",
            "confidence": f"{confidence * 100:.1f}%",
            "factors": raw_factors or {"Anomaly Signature": risk_score}
        }
        
        # Build timeline progression
        timeline_list = [
            {"time": datetime.utcnow().strftime("%H:%M:%S"), "log": f"Entity track registered in {location}."},
            {"time": datetime.utcnow().strftime("%H:%M:%S"), "log": f"Behavior signature flagged for {event_type}."},
            {"time": datetime.utcnow().strftime("%H:%M:%S"), "log": f"Alert emitted with {confidence*100:.0f}% confidence."}
        ]
        
        # Increment threat counts on cameras in that location
        camera = db.query(Camera).filter(Camera.location == location).first()
        if camera:
            camera.threat_count += 1
            camera.safety_score = max(30.0, camera.safety_score - 10.0)
            
        # Update entity risk score
        entity = db.query(AnonymousEntity).filter(AnonymousEntity.entity_id == entity_id).first()
        if entity:
            entity.risk_score = max(entity.risk_score, risk_score)
            
        event = Event(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            location=location,
            entity_id=entity_id,
            risk_score=risk_score,
            confidence=confidence,
            evidence_image=evidence_image,
            reasoning=json.dumps(reasoning_dict),
            timeline=json.dumps(timeline_list),
            status="unresolved",
            is_false_positive=False
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def acknowledge_event(db: Session, event_id: int, user_id: int, username: str, role: str) -> Event:
        """
        Allows security officers to acknowledge an event, creating an audit log.
        """
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return None
            
        event.status = "acknowledged"
        
        # Audit Log
        from backend.engines.audit import AuditEngine
        AuditEngine.log_action(
            db=db,
            action="ACKNOWLEDGE_EVENT",
            reason=f"Security Officer acknowledged alert event #{event_id} ({event.event_type})",
            outcome="success",
            user_id=user_id,
            username=username,
            role=role
        )
        
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def mark_false_positive(db: Session, event_id: int, user_id: int, username: str, role: str, reason: str) -> Event:
        """
        Flags an event as a false positive, feeding back into Explainable AI training data.
        """
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return None
            
        event.status = "false_positive"
        event.is_false_positive = True
        
        # Audit Log
        from backend.engines.audit import AuditEngine
        AuditEngine.log_action(
            db=db,
            action="FALSE_POSITIVE_FLAG",
            reason=f"Flagged event #{event_id} as false positive. Reason: {reason}",
            outcome="success",
            user_id=user_id,
            username=username,
            role=role
        )
        
        db.commit()
        db.refresh(event)
        return event
