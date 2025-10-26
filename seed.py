import uuid
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import Practice, Resource, Service, RecurringAvailability

Base.metadata.create_all(bind=engine)

def seed():
    db: Session = SessionLocal()
    try:
        db.query(RecurringAvailability).delete()
        db.query(Service).delete()
        db.query(Resource).delete()
        db.query(Practice).delete()
        db.commit()

        practice_id = str(uuid.uuid4())
        p = Practice(
            id=practice_id,
            name="Psychologische Praxis Demo",
            city="Berlin",
            time_zone="Europe/Berlin",
            email="kontakt@demo-praxis.de"
        )
        db.add(p)

        svc_id = str(uuid.uuid4())
        s = Service(
            id=svc_id,
            practice_id=practice_id,
            name="Erstgespräch",
            duration_min=50,
            buffer_before_min=0,
            buffer_after_min=10,
            active=True
        )
        db.add(s)

        res_id = str(uuid.uuid4())
        r = Resource(
            id=res_id,
            practice_id=practice_id,
            name="Therapeut/in A",
            active=True
        )
        db.add(r)
        db.commit()

        weekdays = [0,1,2,3,4]  # Mon-Fri
        for wd in weekdays:
            ra = RecurringAvailability(
                id=str(uuid.uuid4()),
                resource_id=res_id,
                weekday=wd,
                start_local="09:00",
                end_local="17:00",
                service_id=svc_id
            )
            db.add(ra)

        db.commit()
        print("Seeded.")
        print("Practice ID:", practice_id)
        print("Service ID:", svc_id)
        print("Resource ID:", res_id)
        print("Use GET /public/practices to fetch details.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
