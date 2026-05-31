class IdentityRequest:
    def __init__(self, request_id: str, requester_name: str, entity_id: str, justification: str, status: str, duration_minutes: int, tenant_id: str):
        self.request_id = request_id
        self.requester_name = requester_name
        self.entity_id = entity_id
        self.justification = justification
        self.status = status
        self.duration_minutes = duration_minutes
        self.tenant_id = tenant_id

class Approval:
    def __init__(self, approval_id: str, request_id: str, approver_name: str, signed_at: str, tenant_id: str):
        self.approval_id = approval_id
        self.request_id = request_id
        self.approver_name = approver_name
        self.signed_at = signed_at
        self.tenant_id = tenant_id

class IdentityRevealSession:
    def __init__(self, reveal_id: str, request_id: str, decrypted_identity: str, expires_at: str, tenant_id: str):
        self.reveal_id = reveal_id
        self.request_id = request_id
        self.decrypted_identity = decrypted_identity
        self.expires_at = expires_at
        self.tenant_id = tenant_id
