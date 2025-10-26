import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Practice, Resource, Service, Appointment
from schemas import PracticeOut, PracticeDetail, SlotOut, AppointmentIn, AppointmentOut
from slot_engine import generate_slots
from zoneinfo import ZoneInfo

from typing import Optional

app = FastAPI(title="Mini Doctolib Backend (Starter)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.lovable\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "PraxisNow API – siehe /health und /docs"}


@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi.routing import APIRoute

@app.get("/_routes")
def list_routes():
    return [r.path for r in app.router.routes]


@app.get("/public/practices", response_model=list[PracticeOut])
def list_practices(db: Session = Depends(get_db)):
    return db.query(Practice).all()

@app.get("/public/practices/{practice_id}", response_model=PracticeDetail)
def practice_detail(practice_id: str, db: Session = Depends(get_db)):
    p = db.query(Practice).filter(Practice.id == practice_id).first()
    if not p:
        raise HTTPException(404, "Practice not found")
    return p

@app.get("/public/practices/{practice_id}/slots", response_model=list[SlotOut])

def practice_slots(
    practice_id: str,
    days: int = Query(14, ge=1, le=60),
    service_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    db: Session = Depends(get_db)
):

    return generate_slots(db, practice_id=practice_id, days=days, service_id=service_id, resource_id=resource_id)

@app.post("/public/appointments", response_model=AppointmentOut)
def book_appointment(payload: AppointmentIn, db: Session = Depends(get_db)):
    # 1) Validierung: gehören alle IDs zur gleichen Praxis?
    p = db.query(Practice).filter(Practice.id == payload.practice_id).first()
    r = db.query(Resource).filter(
        Resource.id == payload.resource_id,
        Resource.practice_id == payload.practice_id
    ).first()
    s = db.query(Service).filter(
        Service.id == payload.service_id,
        Service.practice_id == payload.practice_id
    ).first()
    if not (p and r and s):
        raise HTTPException(400, "Invalid practice/resource/service")

    # 2) Startzeit aus lokalem String parsen
    tz = ZoneInfo(p.time_zone or "Europe/Berlin")
    try:
        start_local = datetime.strptime(payload.start_ts_iso_local, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except ValueError:
        raise HTTPException(400, "Invalid start_ts_iso_local. Use 'YYYY-MM-DD HH:MM'")

    # 3) Endzeit berechnen (Service-Dauer)
    end_local = start_local + timedelta(minutes=s.duration_min)

    # 4) In UTC konvertieren (ohne tzinfo, damit SQLAlchemy sauber vergleicht)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc   = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    # 5) Doppelbuchungs-Check
    exists = db.query(Appointment).filter(
        Appointment.resource_id == payload.resource_id,
        Appointment.start_ts_utc == start_utc,
        Appointment.end_ts_utc == end_utc,
        Appointment.status == "BOOKED"
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Slot already booked")

    # 6) Termin anlegen
    appt = Appointment(
        id=str(uuid.uuid4()),
        practice_id=payload.practice_id,
        resource_id=payload.resource_id,
        service_id=payload.service_id,
        patient_email=payload.patient_email,
        patient_name=payload.patient_name,
        start_ts_utc=start_utc,
        end_ts_utc=end_utc,
        status="BOOKED",
        source="PATIENT"
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # 7) IMMER etwas zurückgeben
    return AppointmentOut(
        id=appt.id,
        start_ts_utc=appt.start_ts_utc,
        end_ts_utc=appt.end_ts_utc,
        status=appt.status
    )


# ---------------------------------------------
# Praxis: Termin stornieren
# ---------------------------------------------
@app.patch("/practice/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    if appt.status == "CANCELLED":
        return AppointmentOut(id=appt.id, start_ts_utc=appt.start_ts_utc, end_ts_utc=appt.end_ts_utc, status=appt.status)
    appt.status = "CANCELLED"
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Cancel conflict")
    db.refresh(appt)
    return AppointmentOut(id=appt.id, start_ts_utc=appt.start_ts_utc, end_ts_utc=appt.end_ts_utc, status=appt.status)

# ---------------------------------------------
# Praxis: Termin verschieben
# ---------------------------------------------
from pydantic import BaseModel

class RescheduleIn(BaseModel):
    new_start_ts_iso_local: str

@app.patch("/practice/appointments/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(appointment_id: str, payload: RescheduleIn, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")

    p = db.query(Practice).filter(Practice.id == appt.practice_id).first()
    s = db.query(Service).filter(Service.id == appt.service_id).first()
    if not (p and s):
        raise HTTPException(400, "Invalid practice/service")

    tz = ZoneInfo(p.time_zone or "Europe/Berlin")
    try:
        new_start_local = datetime.strptime(payload.new_start_ts_iso_local, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except ValueError:
        raise HTTPException(400, "Invalid new_start_ts_iso_local. Use 'YYYY-MM-DD HH:MM'")

    new_end_local = new_start_local + timedelta(minutes=s.duration_min)
    new_start_utc = new_start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    new_end_utc = new_end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    clash = db.query(Appointment).filter(
        Appointment.resource_id == appt.resource_id,
        Appointment.status == "BOOKED",
        Appointment.id != appointment_id,
        Appointment.start_ts_utc == new_start_utc,
        Appointment.end_ts_utc == new_end_utc
    ).first()
    if clash:
        raise HTTPException(409, "New slot already booked")

    appt.start_ts_utc = new_start_utc
    appt.end_ts_utc = new_end_utc
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Reschedule conflict")
    db.refresh(appt)
    return AppointmentOut(id=appt.id, start_ts_utc=appt.start_ts_utc, end_ts_utc=appt.end_ts_utc, status=appt.status)



    tz = ZoneInfo(p.time_zone or "Europe/Berlin")
    try:
        start_local = datetime.strptime(payload.start_ts_iso_local, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except ValueError:
        raise HTTPException(400, "Invalid start_ts_iso_local. Use 'YYYY-MM-DD HH:MM'")

    end_local = start_local + timedelta(minutes=s.duration_min)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    exists = db.query(Appointment).filter(
        Appointment.resource_id == payload.resource_id,
        Appointment.start_ts_utc == start_utc,
        Appointment.end_ts_utc == end_utc,
        Appointment.status == "BOOKED"
    ).first()
    if exists:
        raise HTTPException(409, "Slot already booked")

    appt = Appointment(
        id=str(uuid.uuid4()),
        practice_id=payload.practice_id,
        resource_id=payload.resource_id,
        service_id=payload.service_id,
        patient_email=payload.patient_email,
        patient_name=payload.patient_name,
        start_ts_utc=start_utc,
        end_ts_utc=end_utc,
        status="BOOKED",
        source="PATIENT"
    )
    db.add(appt)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Booking conflict")
    db.refresh(appt)
    return AppointmentOut(id=appt.id, start_ts_utc=appt.start_ts_utc, end_ts_utc=appt.end_ts_utc, status=appt.status)

# ---------------------------------------------
# Praxis: Termine auflisten
# ---------------------------------------------
@app.get("/practice/appointments", response_model=list[AppointmentOut])
def list_appointments(practice_id: str, db: Session = Depends(get_db)):
    items = db.query(Appointment).filter(
        Appointment.practice_id == practice_id,
        Appointment.status == "BOOKED"
    ).order_by(Appointment.start_ts_utc.asc()).all()
    return [
        AppointmentOut(
            id=i.id,
            start_ts_utc=i.start_ts_utc,
            end_ts_utc=i.end_ts_utc,
            status=i.status
        ) for i in items
    ]

