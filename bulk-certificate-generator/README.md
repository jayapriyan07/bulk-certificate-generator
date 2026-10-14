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

The API validates all recipients and processes them independently. A failure for one recipient does not stop the remaining recipients. The response returns the job status, totals, and certificate details with download URLs:

```json
{
  "job_id": 1,
  "status": "completed",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "event_name": "Python Workshop",
  "event_date": "2026-10-08",
  "created_at": "2026-10-14T10:48:00Z",
  "certificates": [
    {
      "id": 1,
      "recipient_name": "Rahul",
      "email": "rahul@example.com",
      "status": "success",
      "error": null,
      "download_url": "/certificates/1"
    },
    {
      "id": 2,
      "recipient_name": "Priya",
      "email": "priya@example.com",
      "status": "success",
      "error": null,
      "download_url": "/certificates/2"
    }
  ]
}
```

## Check job status

GET `/jobs/{job_id}`

The response includes the job details, counts (total, successful, failed), and generated certificate metadata.

## List certificates for a job

GET `/jobs/{job_id}/certificates`

Returns the list of all certificate records for the specified job.

## Retrieve a certificate PDF

GET `/certificates/{certificate_id}`

Downloads the generated PDF certificate (`application/pdf`).

## Check certificate status

GET `/certificates/{certificate_id}/status`

Returns metadata for an individual certificate including its generation status, error (if any), and download link.

## Testing

Run tests with pytest:

```bash
pytest -q
```


## Design decisions

The implementation uses a relational SQLite database with separate Job and Certificate records. Bulk requests are represented by a Job, while each recipient gets an individual Certificate record so success/failure can be tracked independently.

For simplicity and reliability in this assignment, certificate generation is performed in the API process. Each certificate is isolated with its own try/except block, so an individual generation failure does not stop the rest of the bulk job.

For a production system with very large jobs, the generation loop could be moved to a background worker/queue such as Celery or RQ.
