from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ── NEU: Auth ─────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    phone: Optional[str] = None
    address: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class PracticeOut(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    time_zone: str
    class Config:
        from_attributes = True

class ServiceOut(BaseModel):
    id: str
    name: str
    duration_min: int
    buffer_before_min: int
    buffer_after_min: int
    class Config:
        from_attributes = True

class ResourceOut(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True

class PracticeDetail(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    time_zone: str
    services: List[ServiceOut]
    resources: List[ResourceOut]
    class Config:
        from_attributes = True

class SlotOut(BaseModel):
    start_ts: str  # ISO local string
    end_ts: str
    start_ts_utc: datetime
    end_ts_utc: datetime
    resource_id: str
    service_id: str

class AppointmentIn(BaseModel):
    practice_id: str
    resource_id: str
    service_id: str
    start_ts_iso_local: str
    patient_email: Optional[EmailStr] = None
    patient_name: Optional[str] = None

class AppointmentOut(BaseModel):
    id: str
    start_ts_utc: datetime
    end_ts_utc: datetime
    status: str

# ── NEU: Auth ─────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    phone: Optional[str] = None
    address: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None