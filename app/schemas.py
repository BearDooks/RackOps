from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class DeviceBase(BaseModel):
    hostname: str = Field(..., max_length=255)
    make: str = Field(..., max_length=255)
    model: str = Field(..., max_length=255)
    serial_number: str = Field(..., max_length=255)
    ip_address: str = Field(..., max_length=255)
    owner: str = Field(..., max_length=255)
    rack_id: int
    start_u: int
    end_u: int
    depth: str = Field("full", max_length=10)
    position: str = Field("both", max_length=10)
    type: str = Field("Server", max_length=50)
    notes: Optional[str] = None
    oob_ip: Optional[str] = Field(None, max_length=255)
    os: Optional[str] = Field(None, max_length=255)
    asset_tag: Optional[str] = Field(None, max_length=255)

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DeviceSearchResponse(BaseModel):
    id: int
    hostname: str
    make: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = "Server"
    owner: Optional[str] = None
    ip_address: Optional[str] = None
    serial_number: Optional[str] = None
    start_u: int
    end_u: int
    depth: str
    position: str
    rack_id: int
    rack_name: str
    site_id: int
    site_name: str
    notes: Optional[str] = None
    oob_ip: Optional[str] = None
    os: Optional[str] = None
    asset_tag: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RackBase(BaseModel):
    site_id: int
    row: str = Field(..., max_length=50)
    number: str = Field(..., max_length=50)
    total_units: int = 42

class RackCreate(RackBase):
    pass

class Rack(RackBase):
    id: int
    devices: Optional[List[Device]] = None


    model_config = ConfigDict(from_attributes=True)

class SiteBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class SiteCreate(SiteBase):
    pass

class Site(SiteBase):
    id: int
    racks: Optional[List[Rack]] = None


    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserBase(BaseModel):
    username: str = Field(..., max_length=255)
    role: str = Field("Viewer", max_length=20)
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str = Field(..., max_length=255)

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class AuditLogBase(BaseModel):
    timestamp: datetime
    username: str
    action: str
    resource_type: str
    resource_id: int
    details: str

class AuditLog(AuditLogBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
