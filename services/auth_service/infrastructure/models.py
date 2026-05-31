from sqlalchemy import Column, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from services.shared.database import Base, BaseMixin, SoftDeleteMixin, GUID
import datetime

class Permission(Base, BaseMixin):
    __tablename__ = 'permissions'
    permission_key = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)

class Role(Base, BaseMixin):
    __tablename__ = 'roles'
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationship to permission through role_permissions join model
    permissions = relationship('Permission', secondary='role_permissions', back_populates='roles')

class RolePermission(Base, BaseMixin):
    __tablename__ = 'role_permissions'
    role_id = Column(GUID, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(GUID, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)

Permission.roles = relationship('Role', secondary='role_permissions', back_populates='permissions')

class User(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = 'users'
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    role_id = Column(GUID, ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)

    role = relationship('Role')

    # Compatibility properties for password_hash
    @property
    def hashed_password(self) -> str:
        return self.password_hash
    @hashed_password.setter
    def hashed_password(self, value: str):
        self.password_hash = value

    # Compatibility properties for active state
    @property
    def is_active(self) -> bool:
        return self.status == "active"
    @is_active.setter
    def is_active(self, value: bool):
        self.status = "active" if value else "inactive"

    # Compatibility property to support old roles.append() behavior
    @property
    def roles(self):
        class RoleList(list):
            def __init__(self, parent):
                self.parent = parent
                super().__init__([parent.role] if parent.role else [])
            def append(self, role):
                self.parent.role = role
                self.parent.role_id = role.id
                super().append(role)
        return RoleList(self)

class Session(Base, BaseMixin):
    __tablename__ = 'sessions'
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(GUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship('User')

class Notification(Base, BaseMixin):
    __tablename__ = 'notifications'
    
    user_id = Column(GUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    read_status = Column(Boolean, default=False, nullable=False)

    user = relationship('User')
