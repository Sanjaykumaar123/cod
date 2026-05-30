import datetime
from sqlalchemy.orm import Session
from backend.models import IdentityRequest, AnonymousEntity, User
from backend.engines.audit import AuditEngine

class IdentityGovernanceEngine:
    # A list of simulated real identities to reveal upon dual-approval
    MOCK_IDENTITIES = {
        "Entity_93A7": "Johnathan H. Doe (SSN: ***-**-4928) - Status: Clearance Level 2",
        "Entity_2B8C": "Sarah M. Jenkins (ID: 9812A) - SmartCard Registered Staff",
        "Entity_F15E": "Marcus Vance (Driver License: B729119) - Guest Badge #391",
        "Entity_E55A": "Elena Rostova (Passport: 82019A8B) - Restricted Access Contractor"
    }

    @staticmethod
    def create_request(
        db: Session,
        requester_id: int,
        requester_name: str,
        entity_id: str,
        justification: str,
        duration_minutes: int = 30
    ) -> IdentityRequest:
        """
        Submits a formal request to decrypt an anonymous entity's identity.
        Requires justification and dual approvals.
        """
        request = IdentityRequest(
            requester_id=requester_id,
            requester_name=requester_name,
            entity_id=entity_id,
            justification=justification,
            duration_minutes=duration_minutes,
            status="pending",
            created_at=datetime.datetime.utcnow(),
            approved_by_auditor=False,
            approved_by_admin=False
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        
        # Log this governance request in the audit engine
        AuditEngine.log_action(
            db=db,
            action="IDENTITY_DECRYPTION_REQUEST",
            reason=f"Requested decryption access for {entity_id}. Justification: {justification}",
            outcome="success",
            user_id=requester_id,
            username=requester_name,
            role="officer" # Assuming officer role requested
        )
        
        return request

    @staticmethod
    def approve_request(
        db: Session,
        request_id: int,
        approver_id: int,
        approver_name: str,
        role: str
    ) -> IdentityRequest:
        """
        Processes an approval. Requires Auditor AND Admin to fully unlock.
        """
        request = db.query(IdentityRequest).filter(IdentityRequest.id == request_id).first()
        if not request:
            return None
            
        if role == "auditor":
            request.approved_by_auditor = True
            request.approved_by_auditor_name = approver_name
            request.approved_by_auditor_id = approver_id
            AuditEngine.log_action(
                db=db,
                action="IDENTITY_DECRYPTION_AUDITOR_APPROVE",
                reason=f"Auditor approved request #{request_id} for entity {request.entity_id}",
                outcome="success",
                user_id=approver_id,
                username=approver_name,
                role=role
            )
        elif role == "admin":
            request.approved_by_admin = True
            request.approved_by_admin_name = approver_name
            request.approved_by_admin_id = approver_id
            AuditEngine.log_action(
                db=db,
                action="IDENTITY_DECRYPTION_ADMIN_APPROVE",
                reason=f"Admin approved request #{request_id} for entity {request.entity_id}",
                outcome="success",
                user_id=approver_id,
                username=approver_name,
                role=role
            )
            
        # If both approved, elevate status to approved and calculate expiration
        if request.approved_by_auditor and request.approved_by_admin:
            request.status = "approved"
            request.expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=request.duration_minutes)
            
            # Map mock identity to reveal
            real_id = IdentityGovernanceEngine.MOCK_IDENTITIES.get(
                request.entity_id, 
                f"Unknown Subject (Ref: {request.entity_id[-4:]}) - Temporal Visitor Badge"
            )
            request.decrypted_identity = real_id
            
            AuditEngine.log_action(
                db=db,
                action="IDENTITY_DECRYPTION_LEASE_GRANTED",
                reason=f"Dual-key approval complete. Leased decrypt window of {request.duration_minutes} minutes granted.",
                outcome="success",
                user_id=request.requester_id,
                username=request.requester_name,
                role="officer"
            )
            
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def reject_request(
        db: Session,
        request_id: int,
        approver_id: int,
        approver_name: str,
        role: str,
        reason: str
    ) -> IdentityRequest:
        """
        Denies an identity request.
        """
        request = db.query(IdentityRequest).filter(IdentityRequest.id == request_id).first()
        if not request:
            return None
            
        request.status = "rejected"
        
        AuditEngine.log_action(
            db=db,
            action="IDENTITY_DECRYPTION_REJECT",
            reason=f"{role.capitalize()} {approver_name} rejected request #{request_id}. Justification: {reason}",
            outcome="denied",
            user_id=approver_id,
            username=approver_name,
            role=role
        )
        
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def check_identity_access(
        db: Session,
        entity_id: str,
        user: User
    ) -> dict:
        """
        Determines if a user has active decryption access to an entity.
        Only accessible if an active lease exists and is approved, or if the role allows.
        (Actually, policy dictates that even admins must request, but let's see. Let's make it strict!)
        """
        # Audit access check
        now = datetime.datetime.utcnow()
        
        # Look for approved requests containing this entity that haven't expired
        active_lease = db.query(IdentityRequest).filter(
            IdentityRequest.entity_id == entity_id,
            IdentityRequest.status == "approved",
            IdentityRequest.expires_at > now
        ).order_by(IdentityRequest.expires_at.desc()).first()
        
        if active_lease:
            # Audit log success access
            AuditEngine.log_action(
                db=db,
                action="IDENTITY_ACCESS_GRANTED",
                reason=f"Decrypted view for {entity_id} requested by {user.username} (Active Lease: #{active_lease.id})",
                outcome="success",
                user_id=user.id,
                username=user.username,
                role=user.role
            )
            return {
                "permitted": True,
                "decrypted_identity": active_lease.decrypted_identity,
                "expires_in_seconds": int((active_lease.expires_at - now).total_seconds()),
                "lease_id": active_lease.id
            }
            
        # Audit log denied access
        AuditEngine.log_action(
            db=db,
            action="IDENTITY_ACCESS_DENIED",
            reason=f"Decrypted view for {entity_id} denied for {user.username} - No Active Lease.",
            outcome="denied",
            user_id=user.id,
            username=user.username,
            role=user.role
        )
        
        return {
            "permitted": False,
            "decrypted_identity": "[RESTRICTED - IDENTITY SHIELD ACTIVE]",
            "expires_in_seconds": 0,
            "lease_id": None
        }
