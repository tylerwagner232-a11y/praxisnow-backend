from datetime import datetime, timedelta, date
from typing import List, Optional

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from models import Practice, Resource, Service, Appointment
from schemas import SlotOut


def generate_slots(
    db,
    practice_id: str,
    days: int,
    service_id: str,
    resource_id: str
):
    """
    Generiert Slots für eine Praxis für X Tage.
    """
    slots = []

    # Praxis + Service laden
    practice = db.query(Practice).filter(Practice.id == practice_id).first()
    service = db.query(Service).filter(Service.id == service_id).first()
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not practice or not service or not resource:
        return slots  # oder raise

    tz = ZoneInfo(practice.time_zone or "Europe/Berlin")

    # Beispiel: Arbeitszeit 09:00–17:00 (anpassbar)
    work_start_hour = 9
    work_end_hour = 17

    duration = service.duration_min

    today = datetime.now(tz).date()

    for day_offset in range(days):
        current_date = today + timedelta(days=day_offset)

        start_local = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            work_start_hour,
            0,
            tzinfo=tz
        )

        end_local = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            work_end_hour,
            0,
            tzinfo=tz
        )

        # Slot-Schleife
        t = start_local
        while t + timedelta(minutes=duration) <= end_local:
            start_ts_local = t
            end_ts_local = t + timedelta(minutes=duration)

            # UTC konvertieren
            start_utc = start_ts_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            end_utc = end_ts_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            # SlotOut erzeugen – **jetzt korrekt nach deinem Schema**
            slots.append(
                SlotOut(
                    start_ts_utc=start_utc,
                    end_ts_utc=end_utc,
                    resource_id=resource_id,
                    service_id=service_id,
                    is_booked=False
                )
            )

            # nächster Slot
            t = end_ts_local

    return slots
