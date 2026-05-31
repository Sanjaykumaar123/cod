class AuditLog:
    def __init__(self, log_id: str, username: str, role: str, action: str, reason: str, outcome: str, timestamp: str, tenant_id: str):
        self.log_id = log_id
        self.username = username
        self.role = role
        self.action = action
        self.reason = reason
        self.outcome = outcome
        self.timestamp = timestamp
        self.tenant_id = tenant_id

class AuditSession:
    def __init__(self, session_id: str, user_username: str, login_time: str, logout_time: str, ip_address: str, tenant_id: str):
        self.session_id = session_id
        self.user_username = user_username
        self.login_time = login_time
        self.logout_time = logout_time
        self.ip_address = ip_address
        self.tenant_id = tenant_id

class ApprovalHistory:
    def __init__(self, petition_id: str, requester_name: str, approver_name: str, role_signed: str, signed_at: str, status: str, tenant_id: str):
        self.petition_id = petition_id
        self.requester_name = requester_name
        self.approver_name = approver_name
        self.role_signed = role_signed
        self.signed_at = signed_at
        self.status = status
        self.tenant_id = tenant_id
