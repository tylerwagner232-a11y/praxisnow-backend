# slot_engine.py

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from models import Practice, Service, Resource
from schemas import SlotOut


def generate_slots(
    db: Session,
    practice_id: str,
    days: int,
    service_id: str,
    resource_id: str
) -> list[SlotOut]:
    """
    Generiert Slots für eine Praxis für X Tage.

    - verwendet Praxis-Zeitzone (oder Europe/Berlin)
    - nutzt service.duration_min
    - baut Slots zwischen 09:00 und 17:00
    - gibt SlotOut mit start_ts_utc / end_ts_utc / resource_id / service_id / is_booked zurück
    """
    slots: list[SlotOut] = []

    # Praxis / Service / Resource prüfen
    practice = (
        db.query(Practice)
        .filter(Practice.id == practice_id)
        .first()
    )
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )
    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id)
        .first()
    )

    if not practice or not service or not resource:
        # wenn irgendwas nicht passt, einfach keine Slots liefern
        return slots

    tz = ZoneInfo(practice.time_zone or "Europe/Berlin")
    duration_min = service.duration_min

    # Öffnungszeiten (später anpassbar)
    WORK_START_HOUR = 9   # 09:00
    WORK_END_HOUR = 17    # 17:00

    today = datetime.now(tz).date()

    for day_offset in range(days):
        current_date = today + timedelta(days=day_offset)

        day_start_local = datetime(
            year=current_date.year,
            month=current_date.month,
            day=current_date.day,
            hour=WORK_START_HOUR,
            minute=0,
            tzinfo=tz,
        )
        day_end_local = datetime(
            year=current_date.year,
            month=current_date.month,
            day=current_date.day,
            hour=WORK_END_HOUR,
            minute=0,
            tzinfo=tz,
        )

        t = day_start_local
        while t + timedelta(minutes=duration_min) <= day_end_local:
            start_local = t
            end_local = t + timedelta(minutes=duration_min)

            # In UTC konvertieren (tzinfo entfernen, damit DB/Timestamps sauber sind)
            start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            slots.append(
                SlotOut(
                    start_ts_utc=start_utc,
                    end_ts_utc=end_utc,
                    resource_id=resource_id,
                    service_id=service_id,
                    is_booked=False,
                )
            )

            # nächster Slot
            t = end_local

    return slots
