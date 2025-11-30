from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Practice(Base):
    __tablename__ = "practices"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    time_zone = Column(String, nullable=False)

    # Beziehungen
    resources = relationship("Resource", back_populates="practice")
    services = relationship("Service", back_populates="practice")
    appointments = relationship("Appointment", back_populates="practice")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True)
    practice_id = Column(String, ForeignKey("practices.id"), nullable=False, index=True)
    name = Column(String, nullable=False)

    practice = relationship("Practice", back_populates="resources")
    appointments = relationship("Appointment", back_populates="resource")


class Service(Base):
    __tablename__ = "services"

    id = Column(String, primary_key=True)
    practice_id = Column(String, ForeignKey("practices.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    duration_min = Column(Integer, nullable=False)
    buffer_before_min = Column(Integer, default=0)
    buffer_after_min = Column(Integer, default=0)

    practice = relationship("Practice", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")


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

    id = Column(String, primary_key=True)

    practice_id = Column(String, ForeignKey("practices.id"), nullable=False, index=True)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False, index=True)
    service_id = Column(String, ForeignKey("services.id"), nullable=False, index=True)

    patient_email = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    start_ts_utc = Column(DateTime, nullable=False)
    end_ts_utc = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="BOOKED")
    source = Column(String, nullable=True)

    # WICHTIG: saubere Relationships in beide Richtungen
    practice = relationship("Practice", back_populates="appointments")
    resource = relationship("Resource", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
