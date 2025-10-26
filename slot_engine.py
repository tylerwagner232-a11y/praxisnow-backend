from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from typing import List
from sqlalchemy.orm import Session
from models import Practice, Resource, Service, RecurringAvailability, Appointment, Blackout
from schemas import SlotOut

def _daterange(start_date, end_date):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += timedelta(days=1)

def _parse_time(t: str) -> time:
    hh, mm = t.split(":")
    return time(int(hh), int(mm))

from typing import Optional

def generate_slots(db: Session, practice_id: str, days: int = 14, service_id: Optional[str] = None, resource_id: Optional[str] = None) -> List[SlotOut]:

    practice = db.query(Practice).filter(Practice.id == practice_id).first()
    if not practice:
        return []
    tz = ZoneInfo(practice.time_zone or "Europe/Berlin")
    resources_q = db.query(Resource).filter(Resource.practice_id == practice_id, Resource.active == True)
    if resource_id:
        resources_q = resources_q.filter(Resource.id == resource_id)
    resources = resources_q.all()

    services_q = db.query(Service).filter(Service.practice_id == practice_id, Service.active == True)
    if service_id:
        services_q = services_q.filter(Service.id == service_id)
    services = {s.id: s for s in services_q.all()}
    if not services:
        return []

    now_local = datetime.now(tz)
    start_date = now_local.date()
    end_date = start_date + timedelta(days=days)

    slots: List[SlotOut] = []

    for r in resources:
        recs = db.query(RecurringAvailability).filter(RecurringAvailability.resource_id == r.id).all()
        appts = db.query(Appointment).filter(Appointment.resource_id == r.id, Appointment.status == "BOOKED").all()
        blks = db.query(Blackout).filter(Blackout.resource_id == r.id).all()

        booked = [(a.start_ts_utc, a.end_ts_utc) for a in appts]
        blocked = [(b.start_ts, b.end_ts) for b in blks]

        for d in _daterange(start_date, end_date):
            weekday = d.weekday()  # 0=Mon ... 6=Sun
            day_recs = [rec for rec in recs if rec.weekday == weekday]
            for rec in day_recs:
                svc = services.get(rec.service_id) if rec.service_id else (services.get(service_id) if service_id else next(iter(services.values())))
                if not svc:
                    continue
                start_local = datetime.combine(d, _parse_time(rec.start_local), tzinfo=tz)
                end_local = datetime.combine(d, _parse_time(rec.end_local), tzinfo=tz)

                step = svc.duration_min + svc.buffer_before_min + svc.buffer_after_min
                cur = start_local
                while cur + timedelta(minutes=svc.duration_min) <= end_local:
                    slot_start_local = cur
                    slot_end_local = cur + timedelta(minutes=svc.duration_min)

                    ss_utc = slot_start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                    se_utc = slot_end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

                    # collision check
                    col1 = any(not (se_utc <= s or e <= ss_utc) for (s, e) in booked)
                    col2 = any(not (se_utc <= s or e <= ss_utc) for (s, e) in blocked)

                    if not col1 and not col2 and slot_start_local >= now_local:
                        slots.append(SlotOut(
                            start_ts=slot_start_local.strftime("%Y-%m-%d %H:%M"),
                            end_ts=slot_end_local.strftime("%Y-%m-%d %H:%M"),
                            start_ts_utc=slot_start_local.astimezone(ZoneInfo("UTC")),
                            end_ts_utc=slot_end_local.astimezone(ZoneInfo("UTC")),
                            resource_id=r.id,
                            service_id=svc.id
                        ))
                    cur += timedelta(minutes=step)
    return slots
