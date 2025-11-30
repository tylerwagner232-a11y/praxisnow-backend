from datetime import datetime, timedelta, date
from typing import List, Optional

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from models import Practice, Resource, Service, Appointment
from schemas import SlotOut


def generate_slots(
    db: Session,
    practice_id: str,
    days: int = 14,
    service_id: Optional[str] = None,
    resource_id: Optional[str] = None,
) -> List[SlotOut]:
    """
    Einfache Slot-Engine:
    - nimmt eine Praxis
    - wählt eine Resource + Service (oder die per ID)
    - generiert Stundenslots (z. B. 09:00, 10:00, …)
    - entfernt Slots, die bereits in Appointments als BOOKED eingetragen sind
    """

    practice = (
        db.query(Practice)
        .filter(Practice.id == practice_id)
        .first()
    )
    if not practice:
        return []

    # Resource wählen
    if resource_id:
        resource = (
            db.query(Resource)
            .filter(
                Resource.id == resource_id,
                Resource.practice_id == practice_id,
            )
            .first()
        )
    else:
        resource = (
            db.query(Resource)
            .filter(Resource.practice_id == practice_id)
            .first()
        )

    if not resource:
        return []

    # Service wählen
    if service_id:
        service = (
            db.query(Service)
            .filter(
                Service.id == service_id,
                Service.practice_id == practice_id,
            )
            .first()
        )
    else:
        service = (
            db.query(Service)
            .filter(Service.practice_id == practice_id)
            .first()
        )

    if not service:
        return []

    tz = ZoneInfo(practice.time_zone or "Europe/Berlin")

    # Annahme: Dauer + Buffer == 60 Minuten → Slots zur vollen Stunde
    duration_min = service.duration_min or 50

    slots: List[SlotOut] = []

    today = date.today()

    for day_offset in range(days):
        d = today + timedelta(days=day_offset)

        # z.B. 09:00–17:00
        for hour in range(9, 17):  # 9,10,11,12,13,14,15,16
            start_local = datetime(
                d.year, d.month, d.day, hour, 0, tzinfo=tz
            )
            end_local = start_local + timedelta(minutes=duration_min)

            # in UTC umrechnen & tzinfo entfernen (wie im Rest deines Codes)
            start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            # Prüfen, ob dieser Slot schon gebucht ist
            clash = (
                db.query(Appointment)
                .filter(
                    Appointment.resource_id == resource.id,
                    Appointment.start_ts_utc == start_utc,
                    Appointment.end_ts_utc == end_utc,
                    Appointment.status == "BOOKED",
                )
                .first()
            )
            if clash:
                continue

            # SlotOut erwartet typischerweise diese Felder:
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

    return slots
