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
):
    """
    Generiert Standard-Slots für eine Praxis.
    """
    slots = []

    # Praxis / Service / Resource validieren
    practice = db.query(Practice).filter(Practice.id == practice_id).first()
    service = db.query(Service).filter(Service.id == service_id).first()
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not practice or not service or not resource:
        return slots

    tz = ZoneInfo(practice.time_zone or "Europe/Berlin")
    duration = service.duration_min

    # Öffnungszeiten (kannst du später dynamisch machen)
    WORK_START = 9   # 09:00
    WORK_END   = 17  # 17:00

    today = datetime.now(tz).date()

    for day_offset in range(days):
        current_date = today + timedelta(days=day_offset)

        start_local = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            WORK_START, 0,
            tzinfo=tz
        )

        end_local = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            WORK_END, 0,
            tzinfo=tz
        )

        t = start_local
        while t + timedelta(minutes=duration) <= end_local:
            start_ts_local = t
            end_ts_local = t + timedelta(minutes=duration)

            # In UTC konvertieren (tzinfo entfernen!)
            start_utc = start_ts_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            end_utc   = end_ts_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            # Slot hinzufügen
            slots.append(
                SlotOut(
                    start_ts_utc=start_utc,
                    end_ts_utc=end_utc,
                    resource_id=resource_id,
                    service_id=service_id,
                    is_booked=False
                )
            )

            t = end_ts_local  # nächster Slot

    return slots
