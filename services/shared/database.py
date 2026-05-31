import os
from sqlalchemy import create_engine, Column, String, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blindwatch_modular.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

from sqlalchemy import Column, String, DateTime, Boolean
import uuid
import datetime
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified UUIDs.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    return uuid.UUID(value)
                except ValueError:
                    return value
            return value

class BaseMixin:
    """Base class for all multi-tenant tables to inherit UUID primary key and audit timestamps."""
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(GUID, nullable=False, index=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class SoftDeleteMixin:
    """Mixin class to add soft delete support to critical database tables."""
    is_deleted = Column(Boolean, default=False, nullable=False)

class TenantMixin:
    """Legacy mixin class kept for backward compatibility."""
    tenant_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_audit_event(db, user_id, tenant_id, action, target_type, target_id, reason, result="success", ip_address="127.0.0.1"):
    try:
        audit_table = Base.metadata.tables.get('audit_logs')
        if audit_table is not None:
            import uuid
            import datetime
            # Handle string UUIDs
            parsed_tenant_id = tenant_id
            if isinstance(tenant_id, str):
                try:
                    parsed_tenant_id = uuid.UUID(tenant_id)
                except ValueError:
                    parsed_tenant_id = uuid.uuid4()
            elif not tenant_id:
                parsed_tenant_id = uuid.uuid4()

            parsed_user_id = user_id
            if isinstance(user_id, str):
                try:
                    parsed_user_id = uuid.UUID(user_id)
                except ValueError:
                    parsed_user_id = None

            parsed_target_id = target_id
            if isinstance(target_id, str):
                try:
                    parsed_target_id = uuid.UUID(target_id)
                except ValueError:
                    parsed_target_id = None

            db.execute(
                audit_table.insert().values(
                    id=uuid.uuid4(),
                    tenant_id=parsed_tenant_id,
                    user_id=parsed_user_id,
                    action=action,
                    target_type=target_type,
                    target_id=parsed_target_id,
                    reason=reason,
                    result=result,
                    ip_address=ip_address,
                    timestamp=datetime.datetime.utcnow(),
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
            )
            db.commit()
    except Exception as e:
        print(f"Failed to log audit event dynamically: {e}")

