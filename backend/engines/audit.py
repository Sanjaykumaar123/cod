import hashlib
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
        Records an audit event in the database, cryptographically chaining it
        to the previous log to guarantee tamper-resistance.
        """
        # 1. Fetch the last log entry in the database
        last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_log.hash if (last_log and last_log.hash) else "0" * 64
        
        # 2. Instantiate current log (temporary empty hash)
        log = AuditLog(
            user_id=user_id,
            username=username or "SYSTEM",
            role=role or "SERVICE",
            action=action,
            reason=reason,
            timestamp=datetime.utcnow(),
            outcome=outcome,
            ip_address=ip_address,
            previous_hash=prev_hash,
            hash=None
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # 3. Calculate SHA-256 hash using the log elements and the previous hash
        canonical_str = (
            f"{log.id}|{log.username}|{log.role}|{log.action}|"
            f"{log.reason}|{log.outcome}|{log.ip_address}|"
            f"{log.timestamp.isoformat()}|{log.previous_hash}"
        )
        log_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        
        # 4. Save computed hash
        log.hash = log_hash
        db.commit()
        db.refresh(log)
        
        return log

    @staticmethod
    def verify_ledger_integrity(db: Session) -> bool:
        """
        Loops through the audit logs ledger and validates that the hash chain is unbroken.
        Returns True if integral, False if tampered.
        """
        logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
        expected_prev_hash = "0" * 64
        
        for log in logs:
            # Check previous hash link
            if log.previous_hash != expected_prev_hash:
                return False
                
            # Recalculate hash and check
            canonical_str = (
                f"{log.id}|{log.username}|{log.role}|{log.action}|"
                f"{log.reason}|{log.outcome}|{log.ip_address}|"
                f"{log.timestamp.isoformat()}|{log.previous_hash}"
            )
            recalculated = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
            if log.hash != recalculated:
                return False
                
            expected_prev_hash = log.hash
            
        return True

