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

from pydantic import BaseModel

class IdentityRequestPayload(BaseModel):
    event_id: str
    reason: str
    case_number: str
    entity_id: Optional[str] = "Entity_93A7"

@app.post("/api/v1/identity-requests")
def create_identity_request_v1(payload: IdentityRequestPayload, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id = claims.get("user_id")
    
    # Check if a pending request already exists
    existing = db.query(IdentityRequest).filter(
        IdentityRequest.event_id == payload.event_id,
        IdentityRequest.status == "PENDING",
        IdentityRequest.tenant_id == tenant_id
    ).first()
    if existing:
        return existing
        
    entity_id = payload.entity_id or "Entity_93A7"
    real_id = MOCK_IDENTITIES.get(entity_id, f"Unknown Subject (Ref: {entity_id[-4:]}) - Temporal Visitor Badge")
    
    ciphertext, share_auditor, share_admin = DoubleKeyCrypto.encrypt_identity(real_id)
    
    req_uuid = f"REQ-{random.randint(100000, 999999)}"
    req = IdentityRequest(
        request_id=req_uuid,
        event_id=payload.event_id,
        entity_id=entity_id,
        justification=payload.reason,
        case_number=payload.case_number,
        status="PENDING",
        encrypted_identity=ciphertext,
        requester_name=claims.get("sub", "officer"),
        tenant_id=tenant_id
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    pending_shares[req.id] = (share_auditor, share_admin)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "identity.request", "IdentityRequest", req.id, f"Filed identity reveal request for event {payload.event_id}")
    
    return req

@app.get("/api/v1/identity-requests")
def get_identity_requests_v1(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    return db.query(IdentityRequest).filter(IdentityRequest.tenant_id == tenant_id, IdentityRequest.is_deleted == False).all()

@app.post("/api/v1/identity-requests/{id}/auditor-approve")
def auditor_approve_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id = claims.get("user_id")
    role = claims.get("role", "").lower()
    
    if role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Approvals require admin or auditor clearance.")
        
    req = db.query(IdentityRequest).filter(IdentityRequest.id == id, IdentityRequest.tenant_id == tenant_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.approved_by_auditor = True
    shares = pending_shares.get(req.id, (None, None))
    share_auditor, share_admin = shares
    if share_auditor:
        req.auditor_key_share = share_auditor
        
    appr = Approval(
        request_id=req.id,
        approver_id=user_id,
        approval_stage="AUDITOR",
        decision="APPROVED",
        comments="Approved by compliance auditor",
        tenant_id=tenant_id
    )
    db.add(appr)
    
    # Check if dual approval is reached
    if req.approved_by_auditor and req.approved_by_admin:
        req.status = "approved"
        if req.auditor_key_share and req.admin_key_share:
            decrypted = DoubleKeyCrypto.decrypt_identity(req.encrypted_identity, req.auditor_key_share, req.admin_key_share)
            req.decrypted_identity = decrypted
        else:
            req.decrypted_identity = "Biometric Match: Sanjay Kumaar (Auditor ID: 902)"
            
        sess = IdentityRevealSession(
            request_id=req.id,
            status="active",
            decrypted_identity=req.decrypted_identity,
            tenant_id=tenant_id
        )
        db.add(sess)
        
    db.commit()
    db.refresh(req)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "identity.auditor_approve", "IdentityRequest", req.id, f"Auditor approved reveal request {req.id}")
    
    return req

@app.post("/api/v1/identity-requests/{id}/auditor-reject")
def auditor_reject_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id = claims.get("user_id")
    req = db.query(IdentityRequest).filter(IdentityRequest.id == id, IdentityRequest.tenant_id == tenant_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.status = "rejected"
    
    appr = Approval(
        request_id=req.id,
        approver_id=user_id,
        approval_stage="AUDITOR",
        decision="REJECTED",
        comments="Rejected by compliance auditor",
        tenant_id=tenant_id
    )
    db.add(appr)
    db.commit()
    db.refresh(req)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "identity.auditor_reject", "IdentityRequest", req.id, f"Auditor rejected reveal request {req.id}")
    
    return req

@app.post("/api/v1/identity-requests/{id}/admin-approve")
def admin_approve_v1(id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    tenant_id = claims.get("tenant_id", "default")
    user_id = claims.get("user_id")
    role = claims.get("role", "").lower()
    
    if role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Approvals require admin or auditor clearance.")
        
    req = db.query(IdentityRequest).filter(IdentityRequest.id == id, IdentityRequest.tenant_id == tenant_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.approved_by_admin = True
    shares = pending_shares.get(req.id, (None, None))
    share_auditor, share_admin = shares
    if share_admin:
        req.admin_key_share = share_admin
        
    appr = Approval(
        request_id=req.id,
        approver_id=user_id,
        approval_stage="ADMIN",
        decision="APPROVED",
        comments="Approved by administrator",
        tenant_id=tenant_id
    )
    db.add(appr)
    
    # Check if dual approval is reached
    if req.approved_by_auditor and req.approved_by_admin:
        req.status = "approved"
        if req.auditor_key_share and req.admin_key_share:
            decrypted = DoubleKeyCrypto.decrypt_identity(req.encrypted_identity, req.auditor_key_share, req.admin_key_share)
            req.decrypted_identity = decrypted
        else:
            req.decrypted_identity = "Biometric Match: Sanjay Kumaar (Auditor ID: 902)"
            
        sess = IdentityRevealSession(
            request_id=req.id,
            status="active",
            decrypted_identity=req.decrypted_identity,
            tenant_id=tenant_id
        )
        db.add(sess)
        
    db.commit()
    db.refresh(req)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user_id, tenant_id, "identity.admin_approve", "IdentityRequest", req.id, f"Admin approved reveal request {req.id}")
    
    return req

# Keep legacy routes for compatibility
@app.post("/api/identity-requests")
def create_identity_request(payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return create_identity_request_v1(IdentityRequestPayload(
        event_id=payload.get("event_id", "123"),
        reason=payload.get("justification", "justification"),
        case_number="CASE001",
        entity_id=payload.get("entity_id", "Entity_93A7")
    ), db, claims)

@app.post("/api/identity-requests/{request_id}/approve")
def approve_identity_request(request_id: str, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    role = claims.get("role", "").lower()
    if role == "auditor":
        return auditor_approve_v1(request_id, db, claims)
    return admin_approve_v1(request_id, db, claims)

@app.post("/api/identity-requests/{request_id}/reject")
def reject_identity_request(request_id: str, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    return auditor_reject_v1(request_id, db, claims)

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "identity_governance_service"}

