# Bulk Certificate Generator API

A FastAPI backend that accepts a list of certificate recipients, generates PDF certificates from one predefined design, tracks job results, and allows generated certificates to be retrieved.

## Technology
- Python
- FastAPI
- SQLite + SQLAlchemy
- ReportLab
- Pytest

## Setup

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open:
`http://127.0.0.1:8000/docs`

## Create a generation job

POST `/jobs`

Example JSON:
```json
{
  "event_name": "Python Workshop",
  "date": "2026-10-08",
  "recipients": [
    {"name": "Rahul", "email": "rahul@example.com"},
    {"name": "Priya", "email": "priya@example.com"}
  ]
}
```

The API validates all recipients and processes them independently. A failure for one recipient does not stop the remaining recipients.

## Check job status

GET `/jobs/{job_id}`

The response includes total, successful and failed counts.

## Retrieve a certificate

GET `/certificates/{certificate_id}`

The generated PDF is returned for download.

## Testing

```bash
pytest -q
```

## Design decisions

The implementation uses a relational SQLite database with separate Job and Certificate records. Bulk requests are represented by a Job, while each recipient gets an individual Certificate record so success/failure can be tracked independently.

For simplicity and reliability in this assignment, certificate generation is performed in the API process. Each certificate is isolated with its own try/except block, so an individual generation failure does not stop the rest of the bulk job.

For a production system with very large jobs, the generation loop could be moved to a background worker/queue such as Celery or RQ.
