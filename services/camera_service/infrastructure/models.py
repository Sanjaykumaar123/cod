from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Table
from sqlalchemy.orm import relationship
from services.shared.database import Base, TenantMixin

# Association table for Camera-Group relationship
group_cameras = Table(
    'group_cameras',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('camera_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('camera_id', Integer, ForeignKey('cameras.id', ondelete='CASCADE'), primary_key=True)
)

class Camera(Base, TenantMixin):
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    location = Column(String(255), nullable=False)
    rtsp_url = Column(String(255), nullable=False)
    resolution = Column(String(50), default="1920x1080", nullable=False)
    fps = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    privacy_shield_active = Column(Boolean, default=True, nullable=False)
    safety_score = Column(Float, default=100.0, nullable=False)

class CameraGroup(Base, TenantMixin):
    __tablename__ = 'camera_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    cameras = relationship('Camera', secondary=group_cameras)

class CameraStatus(Base, TenantMixin):
    __tablename__ = 'camera_status'

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    issues_logged = Column(String(500), nullable=True)

    camera = relationship('Camera')
