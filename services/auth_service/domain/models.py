class Permission:
    def __init__(self, name: str, description: str, tenant_id: str):
        self.name = name
        self.description = description
        self.tenant_id = tenant_id

class Role:
    def __init__(self, name: str, permissions: list[Permission], tenant_id: str):
        self.name = name
        self.permissions = permissions
        self.tenant_id = tenant_id

class User:
    def __init__(self, username: str, email: str, hashed_password: str, role: Role, full_name: str, is_active: bool, tenant_id: str):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.role = role
        self.full_name = full_name
        self.is_active = is_active
        self.tenant_id = tenant_id

class Session:
    def __init__(self, session_token: str, user_username: str, expires_at: str, tenant_id: str):
        self.session_token = session_token
        self.user_username = user_username
        self.expires_at = expires_at
        self.tenant_id = tenant_id
