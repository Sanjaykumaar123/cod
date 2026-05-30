from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import AuditLog

class AuditEngine:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        reason: str,
        outcome: str,
        user_id: int = None,
        username: str = None,
        role: str = None,
        ip_address: str = "127.0.0.1"
    ) -> AuditLog:
        """
        Records an audit event in the database.
        This is central to the BlindWatch accountability model.
        """
        log = AuditLog(
            user_id=user_id,
            username=username or "SYSTEM",
            role=role or "SERVICE",
            action=action,
            reason=reason,
            timestamp=datetime.utcnow(),
            outcome=outcome,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
