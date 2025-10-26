# Mini Doctolib Backend (Starter)

A minimal booking backend with FastAPI + SQLite. Patients and practices share the same data → automatic sync.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn main:app --reload
```
Open http://127.0.0.1:8000/docs

## Endpoints
- GET /public/practices
- GET /public/practices/{practice_id}
- GET /public/practices/{practice_id}/slots?days=14&service_id=&resource_id=
- POST /public/appointments

Switch to Postgres later by changing DATABASE_URL.
