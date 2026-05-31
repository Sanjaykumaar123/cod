import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from services.shared.database import get_db, Base, engine, SessionLocal
from services.auth_service.infrastructure.models import User, Role, Permission

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "blindwatch_super_secret_cybersecurity_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
SALT = "blindwatch_salt_security_layer_2026"

app = FastAPI(title="BlindWatch Auth Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def get_password_hash(password: str) -> str:
    salted = password + SALT
    return hashlib.sha256(salted.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.on_event("startup")
def startup_seed():
    # Make sure tables are created

    db = SessionLocal()
    try:
        if not db.query(User).first():
            print("Seeding default roles and users in modular db...")
            # Create default roles
            admin_role = Role(name="admin", description="Full system access", tenant_id="default")
            auditor_role = Role(name="auditor", description="Audit logs and decrypt signs access", tenant_id="default")
            officer_role = Role(name="officer", description="Filing decrypt requests access", tenant_id="default")
            viewer_role = Role(name="viewer", description="Read-only operations access", tenant_id="default")
            
            db.add_all([admin_role, auditor_role, officer_role, viewer_role])
            db.commit()
            
            # Create default users
            users_data = [
                ("admin", "admin123", "admin@blindwatch.ai", admin_role, "System Administrator"),
                ("auditor", "auditor123", "auditor@blindwatch.ai", auditor_role, "Compliance Auditor"),
                ("officer", "officer123", "officer@blindwatch.ai", officer_role, "Security Officer"),
                ("viewer", "viewer123", "viewer@blindwatch.ai", viewer_role, "Executive Observer")
            ]
            
            for username, pwd, email, role, name in users_data:
                user = User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    is_active=True,
                    tenant_id="default"
                )
                user.roles.append(role)
                db.add(user)
            db.commit()
            print("Modular db seeding complete.")
    finally:
        db.close()

from pydantic import BaseModel

class LoginPayload(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class UserCreatePayload(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_name: Optional[str] = "viewer"

class UserUpdatePayload(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_name: Optional[str] = None
    status: Optional[str] = None

@app.post("/api/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role_name = user.roles[0].name.upper() if user.roles else "VIEWER"
    token = create_access_token(data={"sub": user.username, "role": role_name, "tenant_id": str(user.tenant_id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": role_name,
        "full_name": user.full_name
    }

@app.post("/api/v1/auth/login")
def login_v1(payload: LoginPayload, db: Session = Depends(get_db)):
    user = None
    if payload.email:
        user = db.query(User).filter(User.email == payload.email).first()
    if not user and payload.username:
        user = db.query(User).filter(User.username == payload.username).first()
    if not user and payload.email:
        user = db.query(User).filter(User.username == payload.email).first()
        
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email/username or password")
        
    role_name = user.roles[0].name.upper() if user.roles else "VIEWER"
    token = create_access_token(data={"sub": user.username, "role": role_name, "tenant_id": str(user.tenant_id)})
    
    from services.shared.database import log_audit_event
    log_audit_event(db, user.id, user.tenant_id, "user.login", "User", user.id, f"User {user.username} logged in successfully.")
    
    return {
        "access_token": token,
        "refresh_token": token,
        "role": role_name,
        "username": user.username,
        "full_name": user.full_name
    }


@app.post("/api/v1/auth/refresh")
def refresh_v1(claims: User = Depends(get_current_user)):
    role_name = claims.roles[0].name.upper() if claims.roles else "VIEWER"
    token = create_access_token(data={"sub": claims.username, "role": role_name, "tenant_id": str(claims.tenant_id)})
    return {
        "access_token": token,
        "refresh_token": token,
        "role": role_name
    }

@app.post("/api/v1/auth/logout")
def logout_v1(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from services.shared.database import log_audit_event
    log_audit_event(db, current_user.id, current_user.tenant_id, "user.logout", "User", current_user.id, f"User {current_user.username} logged out.")
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/api/v1/users")
def get_users_v1(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_name = current_user.roles[0].name.upper() if current_user.roles else "VIEWER"
    if role_name != "ADMIN":
        raise HTTPException(status_code=403, detail="Permission denied: Admins only")
    return db.query(User).filter(User.is_deleted == False).all()

@app.post("/api/v1/users")
def create_user_v1(payload: UserCreatePayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_name_curr = current_user.roles[0].name.upper() if current_user.roles else "VIEWER"
    if role_name_curr != "ADMIN":
        raise HTTPException(status_code=403, detail="Permission denied: Admins only")
        
    role_obj = db.query(Role).filter(Role.name == payload.role_name.lower()).first()
    if not role_obj:
        role_obj = Role(name=payload.role_name.lower(), description="Custom role", tenant_id=current_user.tenant_id)
        db.add(role_obj)
        db.commit()
        db.refresh(role_obj)
        
    new_user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role_id=role_obj.id,
        status="active",
        tenant_id=current_user.tenant_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, current_user.id, current_user.tenant_id, "user.create", "User", new_user.id, f"Created new user {new_user.username}")
    
    return new_user

@app.put("/api/v1/users/{id}")
def update_user_v1(id: str, payload: UserUpdatePayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_name_curr = current_user.roles[0].name.upper() if current_user.roles else "VIEWER"
    if role_name_curr != "ADMIN":
        raise HTTPException(status_code=403, detail="Permission denied: Admins only")
        
    user = db.query(User).filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if payload.email:
        user.email = payload.email
    if payload.username:
        user.username = payload.username
    if payload.full_name:
        user.full_name = payload.full_name
    if payload.phone:
        user.phone = payload.phone
    if payload.status:
        user.status = payload.status
    if payload.role_name:
        role_obj = db.query(Role).filter(Role.name == payload.role_name.lower()).first()
        if role_obj:
            user.role_id = role_obj.id
            
    db.commit()
    db.refresh(user)
    
    from services.shared.database import log_audit_event
    log_audit_event(db, current_user.id, current_user.tenant_id, "user.update", "User", user.id, f"Updated user parameters for {user.username}")
    
    return user

@app.delete("/api/v1/users/{id}")
def delete_user_v1(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_name_curr = current_user.roles[0].name.upper() if current_user.roles else "VIEWER"
    if role_name_curr != "ADMIN":
        raise HTTPException(status_code=403, detail="Permission denied: Admins only")
        
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_deleted = True
    db.commit()
    
    from services.shared.database import log_audit_event
    log_audit_event(db, current_user.id, current_user.tenant_id, "user.delete", "User", user.id, f"Soft deleted user {user.username}")
    
    return {"status": "success", "message": f"User {user.username} soft deleted successfully."}

@app.get("/api/v1/users/me")
def read_users_me_v1(current_user: User = Depends(get_current_user)):
    role_name = current_user.roles[0].name if current_user.roles else "viewer"
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": role_name,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "tenant_id": current_user.tenant_id
    }

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "auth_service"}
