from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from .database import Base

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    racks = relationship("Rack", back_populates="site", cascade="all, delete-orphan")


class Rack(Base):
    __tablename__ = "racks"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    row = Column(String)
    number = Column(String)
    total_units = Column(Integer, default=42)

    site = relationship("Site", back_populates="racks")
    devices = relationship("Device", back_populates="rack", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    make = Column(String)
    model = Column(String)
    serial_number = Column(String, index=True)
    ip_address = Column(String, index=True)
    owner = Column(String, index=True)
    rack_id = Column(Integer, ForeignKey("racks.id"))
    start_u = Column(Integer)
    end_u = Column(Integer)
    depth = Column(String, default="full")  # "full" or "half"
    position = Column(String, default="both")  # "front", "back", "both"
    type = Column(String, default="Server")  # "Server", "Network", "Storage", "Patch Panel", "PDU"
    
    # New fields
    notes = Column(String, nullable=True)
    oob_ip = Column(String, index=True, nullable=True)
    os = Column(String, index=True, nullable=True)
    asset_tag = Column(String, index=True, nullable=True)

    rack = relationship("Rack", back_populates="devices")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="Viewer") # "Viewer" or "Editor"
    is_active = Column(Boolean, default=True)
    tooltips_enabled = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    username = Column(String, index=True)
    action = Column(String) # "CREATE", "UPDATE", "DELETE"
    resource_type = Column(String) # "Site", "Rack", "Device"
    resource_id = Column(Integer)
    details = Column(String)
