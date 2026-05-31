import os
import hashlib
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from services.shared.database import get_db, Base, engine, SessionLocal
from services.audit_service.infrastructure.models import AuditLog

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

app = FastAPI(title="BlindWatch Audit Service", version="1.0.0")

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
        raise HTTPException(status_code=401, detail="Invalid token claims")

def calculate_log_hash(log: AuditLog) -> str:
    # Use canonical format
    ts_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(log.timestamp, datetime) else str(log.timestamp)
    canonical = f"{log.id}|{log.username}|{log.role}|{log.action}|{log.reason}|{log.outcome}|{log.ip_address}|{ts_str}|{log.previous_hash}"
    return hashlib.sha256(canonical.encode()).hexdigest()

def insert_log(db: Session, action: str, reason: str, outcome: str, user_id: Optional[int], username: str, role: str, tenant_id: str = "default", ip: str = "127.0.0.1") -> AuditLog:
    # Fetch last log
    last_log = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.hash if last_log else "GENESIS_BLOCK"
    
    log = AuditLog(
        user_id=user_id,
        username=username,
        role=role,
        action=action,
        reason=reason,
        outcome=outcome,
        ip_address=ip,
        previous_hash=prev_hash,
        tenant_id=tenant_id
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # Calculate hash and update
    log.hash = calculate_log_hash(log)
    db.commit()
    db.refresh(log)
    return log

@app.on_event("startup")
def seed_audit_logs():

    db = SessionLocal()
    try:
        if not db.query(AuditLog).first():
            print("Seeding initial cryptographic audit ledger logs...")
            insert_log(
                db=db,
                action="SYSTEM_INIT",
                reason="BlindWatch Modular Microservices Operating System initiated.",
                outcome="success",
                user_id=0,
                username="system",
                role="system",
                tenant_id="default"
            )
            insert_log(
                db=db,
                action="DATABASE_SETUP",
                reason="SQL tables created. Tenant schema separation checks validated.",
                outcome="success",
                user_id=0,
                username="system",
                role="system",
                tenant_id="default"
            )
            print("Audit logs initialized.")
    finally:
        db.close()

@app.get("/api/v1/audit/logs")
def get_audit_logs_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    role = claims.get("role", "").upper()
    if role not in ["ADMIN", "AUDITOR"]:
         raise HTTPException(status_code=403, detail="Unprivileged access denied to system audit trail.")
    tenant_id = claims.get("tenant_id", "default")
    return db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.created_at.desc()).all()

@app.post("/api/v1/audit/verify")
def verify_audit_ledger_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    role = claims.get("role", "").upper()
    if role not in ["ADMIN", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Unprivileged access denied.")
    tenant_id = claims.get("tenant_id", "default")
    
    logs = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.id.asc()).all()
    
    is_valid = True
    expected_prev = "GENESIS_BLOCK"
    
    for log in logs:
        if log.previous_hash != expected_prev:
            is_valid = False
            break
        computed = calculate_log_hash(log)
        if log.hash != computed:
            is_valid = False
            break
        expected_prev = log.hash
        
    insert_log(
        db=db,
        action="AUDIT_LEDGER_VERIFIED",
        reason=f"Cryptographic integrity audit conducted by {claims.get('sub')}. Integrity status: {is_valid}",
        outcome="success" if is_valid else "failed",
        user_id=None,
        username=claims.get("sub", "auditor"),
        role=claims.get("role", "auditor"),
        tenant_id=tenant_id
    )
    
    return {
        "integrity_verified": is_valid,
        "algorithm": "SHA-256 Hash Chain",
        "timestamp": datetime.utcnow().isoformat()
    }

# Keep legacy routes for compatibility
@app.get("/api/audit-logs")
def get_audit_logs(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return get_audit_logs_v1(db, claims)

@app.post("/api/audit-logs/log")
def create_audit_log_entry(payload: dict, db: Session = Depends(get_db)):
    log = insert_log(
        db=db,
        action=payload.get("action"),
        reason=payload.get("reason"),
        outcome=payload.get("outcome", "success"),
        user_id=payload.get("user_id"),
        username=payload.get("username", "system"),
        role=payload.get("role", "system"),
        tenant_id=payload.get("tenant_id", "default"),
        ip=payload.get("ip_address", "127.0.0.1")
    )
    return {"status": "logged", "id": str(log.id), "hash": log.hash}

@app.post("/api/audit-logs/verify")
def verify_audit_ledger(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return verify_audit_ledger_v1(db, claims)

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "audit_service"}

