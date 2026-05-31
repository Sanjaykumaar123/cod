from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from services.shared.database import Base, TenantMixin

# Association table for User-Role relationship in a multi-tenant setting
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for Role-Permission relationship in a multi-tenant setting
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)

class Permission(Base, TenantMixin):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

class Role(Base, TenantMixin):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)

    permissions = relationship('Permission', secondary=role_permissions)

class User(Base, TenantMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    mfa_secret = Column(String(100), nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)

    roles = relationship('Role', secondary=user_roles)

class Session(Base, TenantMixin):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expires_at = Column(String(100), nullable=False)

    user = relationship('User')
