from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Text, DateTime, Integer
from sqlalchemy.orm import relationship
from services.shared.database import Base, BaseMixin, SoftDeleteMixin, GUID

class Camera(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = 'cameras'

    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    camera_type = Column(String(50), default="RTSP", nullable=False)  # WEBCAM, RTSP, VIDEO_UPLOAD
    stream_url = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    health_score = Column(Float, default=100.0, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Specific attributes from earlier features and frontend requirements
    privacy_shield_active = Column(Boolean, default=True, nullable=False)
    resolution = Column(String(50), default="1920x1080", nullable=True)
    fps = Column(Integer, default=30, nullable=True)

    # Backward compatibility properties
    @property
    def rtsp_url(self) -> str:
        return self.stream_url
    @rtsp_url.setter
    def rtsp_url(self, value: str):
        self.stream_url = value

    @property
    def is_active(self) -> bool:
        return self.status == "active"
    @is_active.setter
    def is_active(self, value: bool):
        self.status = "active" if value else "offline"

    @property
    def safety_score(self) -> float:
        return self.health_score
    @safety_score.setter
    def safety_score(self, value: float):
        self.health_score = value

class CameraGroup(Base, BaseMixin):
    __tablename__ = 'camera_groups'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    cameras = relationship('Camera', secondary='camera_group_members', back_populates='groups')

class CameraGroupMember(Base, BaseMixin):
    __tablename__ = 'camera_group_members'

    group_id = Column(GUID, ForeignKey('camera_groups.id', ondelete='CASCADE'), nullable=False)
    camera_id = Column(GUID, ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False)

Camera.groups = relationship('CameraGroup', secondary='camera_group_members', back_populates='cameras')

class CameraStatus(Base, BaseMixin):
    __tablename__ = 'camera_status'

    camera_id = Column(GUID, ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    issues_logged = Column(String(500), nullable=True)

    camera = relationship('Camera')
