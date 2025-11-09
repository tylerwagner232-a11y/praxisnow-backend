from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import datetime as dt

class Practice(Base):
    __tablename__ = "practices"
    id = Column(String, primary_key=True)
    name = Column(Text, nullable=False)
    street = Column(Text)
    postal_code = Column(Text)
    city = Column(Text)
    state = Column(Text)
    country = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    time_zone = Column(Text, nullable=False, default="Europe/Berlin")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    services = relationship("Service", back_populates="practice", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="practice", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    id = Column(String, primary_key=True)
    practice_id = Column(String, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    duration_min = Column(Integer, nullable=False)
    buffer_before_min = Column(Integer, nullable=False, default=0)
    buffer_after_min = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    practice = relationship("Practice", back_populates="services")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(String, primary_key=True)
    practice_id = Column(String, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    color = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    practice = relationship("Practice", back_populates="resources")
    recurring = relationship("RecurringAvailability", back_populates="resource", cascade="all, delete-orphan")
    blackouts = relationship("Blackout", back_populates="resource", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="resource", cascade="all, delete-orphan")

class RecurringAvailability(Base):
    __tablename__ = "recurring_availability"
    id = Column(String, primary_key=True)
    resource_id = Column(String, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=Mon ... 6=Sun
    start_local = Column(Text, nullable=False) # '09:00'
    end_local = Column(Text, nullable=False)   # '17:00'
    service_id = Column(String, ForeignKey("services.id"))

    resource = relationship("Resource", back_populates="recurring")

class Blackout(Base):
    __tablename__ = "blackout"
    id = Column(String, primary_key=True)
    resource_id = Column(String, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    start_ts = Column(DateTime, nullable=False)  # UTC
    end_ts = Column(DateTime, nullable=False)    # UTC
    reason = Column(Text)
    resource = relationship("Resource", back_populates="blackouts")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = {'extend_existing': True}
    id = Column(String, primary_key=True)
    practice_id = Column(String, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False)
    service_id = Column(String, ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    patient_email = Column(Text)
    patient_name = Column(Text)
    start_ts_utc = Column(DateTime, nullable=False)
    end_ts_utc = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False, default="BOOKED")  # BOOKED, CANCELLED, COMPLETED, NOSHOW
    source = Column(Text, nullable=False, default="PATIENT") # PATIENT or STAFF
    notes_internal = Column(Text)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    resource = relationship("Resource", back_populates="appointments")
    __table_args__ = (UniqueConstraint("resource_id", "start_ts_utc", "end_ts_utc", name="uq_no_double_booking"),)
