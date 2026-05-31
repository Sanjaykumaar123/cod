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

    # Transient memory vault for pending key shares before they are signed/approved
    _pending_shares = {}

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
        Generates cryptographic key shares and stores them in the pending vault.
        """
        # Map mock identity to encrypt
        real_id = IdentityGovernanceEngine.MOCK_IDENTITIES.get(
            entity_id, 
            f"Unknown Subject (Ref: {entity_id[-4:]}) - Temporal Visitor Badge"
        )
        
        # Cryptographic encrypt and split
        from backend.crypto import DoubleKeyCrypto
        ciphertext, share_auditor, share_admin = DoubleKeyCrypto.encrypt_identity(real_id)

        request = IdentityRequest(
            requester_id=requester_id,
            requester_name=requester_name,
            entity_id=entity_id,
            justification=justification,
            duration_minutes=duration_minutes,
            status="pending",
            created_at=datetime.datetime.utcnow(),
            approved_by_auditor=False,
            approved_by_admin=False,
            encrypted_identity=ciphertext,
            auditor_key_share=None,
            admin_key_share=None
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        
        # Store shares in the transient vault indexed by database request ID
        IdentityGovernanceEngine._pending_shares[request.id] = (share_auditor, share_admin)
        
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
        Processes an approval. Releases the respective cryptographic share to the DB.
        Decrypts the identity using the combined shares once both approvals are recorded.
        """
        request = db.query(IdentityRequest).filter(IdentityRequest.id == request_id).first()
        if not request:
            return None

        # Retrieve shares from vault if present (fallback to random if already removed/processed)
        shares = IdentityGovernanceEngine._pending_shares.get(request_id, (None, None))
        share_auditor, share_admin = shares
            
        if role == "auditor":
            request.approved_by_auditor = True
            request.approved_by_auditor_name = approver_name
            request.approved_by_auditor_id = approver_id
            if share_auditor:
                request.auditor_key_share = share_auditor
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
            if share_admin:
                request.admin_key_share = share_admin
            AuditEngine.log_action(
                db=db,
                action="IDENTITY_DECRYPTION_ADMIN_APPROVE",
                reason=f"Admin approved request #{request_id} for entity {request.entity_id}",
                outcome="success",
                user_id=approver_id,
                username=approver_name,
                role=role
            )
            
        # If both approved, elevate status to approved, combine shares, and decrypt
        if request.approved_by_auditor and request.approved_by_admin:
            request.status = "approved"
            request.expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=request.duration_minutes)
            
            # Combine the Auditor and Admin shares to reconstruct the key and decrypt
            from backend.crypto import DoubleKeyCrypto
            if request.auditor_key_share and request.admin_key_share:
                decrypted = DoubleKeyCrypto.decrypt_identity(
                    request.encrypted_identity,
                    request.auditor_key_share,
                    request.admin_key_share
                )
                request.decrypted_identity = decrypted
            else:
                request.decrypted_identity = "[DECRYPTION ERROR: MISSING KEY SHARES]"
            
            # Clean up the transient vault
            if request_id in IdentityGovernanceEngine._pending_shares:
                del IdentityGovernanceEngine._pending_shares[request_id]
            
            AuditEngine.log_action(
                db=db,
                action="IDENTITY_DECRYPTION_LEASE_GRANTED",
                reason=f"Dual-key approval complete. Cryptographic lease granted.",
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
