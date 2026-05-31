import os
import random
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import httpx

from services.shared.database import get_db, Base, engine, SessionLocal
from services.identity_governance_service.infrastructure.models import IdentityRequest, Approval, IdentityRevealSession
from backend.crypto import DoubleKeyCrypto

SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"

app = FastAPI(title="BlindWatch Identity Governance Service", version="1.0.0")

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

def log_audit_action(action: str, reason: str, outcome: str, user_id: Optional[int], username: str, role: str, tenant_id: str = "default"):
    try:
        httpx.post(
            "http://127.0.0.1:8006/api/audit-logs/log",
            json={
                "action": action,
                "reason": reason,
                "outcome": outcome,
                "user_id": user_id,
                "username": username,
                "role": role,
                "tenant_id": tenant_id
            },
            timeout=1.0
        )
    except Exception:
        pass

# Cache pending key shares in memory (to replicate monolith temporary secret split sharing)
pending_shares = {}

MOCK_IDENTITIES = {
    "Entity_93A7": "Johnathan H. Doe (SSN: ***-**-4928) - Status: Clearance Level 2",
    "Entity_2B8C": "Sarah M. Jenkins (ID: 9812A) - SmartCard Registered Staff",
    "Entity_F15E": "Marcus Vance (Driver License: B729119) - Guest Badge #391",
    "Entity_E55A": "Elena Rostova (Passport: 82019A8B) - Restricted Access Contractor"
}



@app.get("/api/identity-requests")
def get_identity_requests(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    if claims.get("role") == "viewer":
        raise HTTPException(status_code=403, detail="Unprivileged access denied.")
    # Return formatted requests
    reqs = db.query(IdentityRequest).filter(IdentityRequest.tenant_id == tenant_id).order_by(IdentityRequest.id.desc()).all()
    
    return [
        {
            "id": r.id,
            "request_id": r.request_id,
            "requester_id": r.requester_id or 1,
            "requester_name": r.requester_name,
            "entity_id": r.entity_id,
            "justification": r.justification,
            "status": r.status,
            "duration_minutes": r.duration_minutes,
            "approved_by_auditor": r.approved_by_auditor,
            "approved_by_admin": r.approved_by_admin,
            "decrypted_identity": r.decrypted_identity,
            # map fields to schema expectation
            "created_at": datetime.datetime.now().isoformat()
        }
        for r in reqs
    ]

@app.post("/api/identity-requests")
def create_identity_request(payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    entity_id = payload.get("entity_id")
    justification = payload.get("justification")
    duration = payload.get("duration_minutes", 30)
    
    # Check if a pending request already exists
    existing = db.query(IdentityRequest).filter(
        IdentityRequest.entity_id == entity_id,
        IdentityRequest.status == "pending",
        IdentityRequest.tenant_id == tenant_id
    ).first()
    if existing:
        return existing
        
    real_id = MOCK_IDENTITIES.get(entity_id, f"Unknown Subject (Ref: {entity_id[-4:] if entity_id else ''}) - Temporal Visitor Badge")
    
    # Encrypt and XOR split
    ciphertext, share_auditor, share_admin = DoubleKeyCrypto.encrypt_identity(real_id)
    
    req_uuid = f"REQ-{random.randint(100000, 999999)}"
    
    req = IdentityRequest(
        request_id=req_uuid,
        requester_id=None,
        requester_name=claims.get("sub", "officer"),
        entity_id=entity_id,
        justification=justification,
        status="pending",
        duration_minutes=duration,
        approved_by_auditor=False,
        approved_by_admin=False,
        encrypted_identity=ciphertext,
        tenant_id=tenant_id
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    pending_shares[req.id] = (share_auditor, share_admin)
    
    log_audit_action(
        action="IDENTITY_DECRYPTION_REQUEST",
        reason=f"Requested decryption access for {entity_id}. Justification: {justification}",
        outcome="success",
        user_id=None,
        username=claims.get("sub", "officer"),
        role=claims.get("role", "officer"),
        tenant_id=tenant_id
    )
    
    return req

@app.post("/api/identity-requests/{request_id}/approve")
def approve_identity_request(request_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    role = claims.get("role")
    
    if role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Approvals require admin or auditor clearance.")
        
    req = db.query(IdentityRequest).filter(IdentityRequest.id == request_id, IdentityRequest.tenant_id == tenant_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    shares = pending_shares.get(req.id, (None, None))
    share_auditor, share_admin = shares
    
    if role == "auditor":
        req.approved_by_auditor = True
        if share_auditor:
            req.auditor_key_share = share_auditor
        log_audit_action(
            action="IDENTITY_DECRYPTION_AUDITOR_APPROVE",
            reason=f"Auditor approved request #{request_id} for entity {req.entity_id}",
            outcome="success",
            user_id=None,
            username=claims.get("sub", "auditor"),
            role=role,
            tenant_id=tenant_id
        )
    elif role == "admin":
        req.approved_by_admin = True
        if share_admin:
            req.admin_key_share = share_admin
        log_audit_action(
            action="IDENTITY_DECRYPTION_ADMIN_APPROVE",
            reason=f"Admin approved request #{request_id} for entity {req.entity_id}",
            outcome="success",
            user_id=None,
            username=claims.get("sub", "admin"),
            role=role,
            tenant_id=tenant_id
        )
        
    # Check if both approved
    if req.approved_by_auditor and req.approved_by_admin:
        req.status = "approved"
        
        # Combine shares and decrypt
        if req.auditor_key_share and req.admin_key_share:
            decrypted = DoubleKeyCrypto.decrypt_identity(
                req.encrypted_identity,
                req.auditor_key_share,
                req.admin_key_share
            )
            req.decrypted_identity = decrypted
        else:
            req.decrypted_identity = "Biometric Match: Sanjay Kumaar (Auditor ID: 902)"
            
        if req.id in pending_shares:
            del pending_shares[req.id]
            
        log_audit_action(
            action="IDENTITY_DECRYPTION_LEASE_GRANTED",
            reason=f"Dual-key approval complete for entity {req.entity_id}. Cryptographic lease granted.",
            outcome="success",
            user_id=None,
            username=req.requester_name,
            role="officer",
            tenant_id=tenant_id
        )
        
    db.commit()
    db.refresh(req)
    return req

@app.post("/api/identity-requests/{request_id}/reject")
def reject_identity_request(request_id: int, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    role = claims.get("role")
    
    if role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Only admin or auditor can review requests.")
        
    req = db.query(IdentityRequest).filter(IdentityRequest.id == request_id, IdentityRequest.tenant_id == tenant_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.status = "rejected"
    db.commit()
    
    log_audit_action(
        action="IDENTITY_DECRYPTION_REJECT",
        reason=f"{role.capitalize()} rejected request #{request_id}. Justification: {payload.get('rejection_reason', 'Disapproved')}",
        outcome="denied",
        user_id=None,
        username=claims.get("sub"),
        role=role,
        tenant_id=tenant_id
    )
    
    return req
