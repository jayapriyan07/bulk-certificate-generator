# Bulk Certificate Generator API

A robust FastAPI backend service that accepts a list of certificate recipients, asynchronously generates elegant PDF certificates with unique identifiers, tracks job progress and results, and allows generated certificates to be queried and downloaded.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-lightgrey.svg)](https://www.sqlalchemy.org/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF-red.svg)](https://www.reportlab.com/)
[![Tests](https://img.shields.io/badge/Pytest-11%20Passed-brightgreen.svg)](https://pytest.org/)

---

## Features

- **Bulk Certificate Generation**: Submit single or batch certificate generation requests for events, workshops, and webinars.
- **Independent Recipient Processing**: Each certificate is generated independently in an isolated try-catch block; failure for one recipient does not fail the batch.
- **Dynamic Text Fitting & Typography**: Auto-scales text sizing for long recipient names and event titles to eliminate margin overflows.
- **Professional PDF Design**: High-resolution vector PDF certificate generation featuring dual-tone borders (navy blue & soft gold) and structured metadata.
- **Detailed Job & Certificate Tracking**: Real-time tracking of job status (`processing`, `completed`, `failed`), recipient counts, individual certificate generation status, error reasons, and direct download links.
- **Zero Pollution Isolated Test Suite**: 100% test isolation using in-memory SQLite (`sqlite:///:memory:`) and temporary directory fixtures.

---

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database & ORM**: SQLite with [SQLAlchemy](https://www.sqlalchemy.org/)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **PDF Generation**: [ReportLab](https://www.reportlab.com/)
- **Testing**: [Pytest](https://pytest.org/) & [HTTPX](https://www.python-httpx.org/)

---

## Project Structure

```text
bulk-certificate-generator/
├── bulk-certificate-generator/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py       # SQLAlchemy engine & session setup (absolute paths)
│   │   ├── main.py           # FastAPI routes & error handlers
│   │   ├── models.py         # Job and Certificate relational ORM models
│   │   ├── schemas.py        # Pydantic validation schemas
│   │   └── services.py       # ReportLab PDF certificate rendering engine
│   ├── tests/
│   │   └── test_api.py       # Isolated Pytest test suite (11 test cases)
│   ├── generated/            # Output folder for generated PDF files
│   ├── requirements.txt      # Project dependencies
│   ├── pytest.ini            # Subdirectory Pytest config
│   └── README.md
├── pytest.ini                # Root Pytest config
├── .gitignore                # Git ignore configuration
└── README.md                 # Root repository documentation
```

---

## Quick Start

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/jayapriyan07/bulk-certificate-generator.git
cd bulk-certificate-generator

# Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r bulk-certificate-generator/requirements.txt
```

### 3. Run the API Server

From the `bulk-certificate-generator` project folder:
```bash
cd bulk-certificate-generator
uvicorn app.main:app --reload
```

The server will be available at:
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

### 1. Create a Generation Job

`POST /jobs`

**Request Body:**
```json
{
  "event_name": "Full Stack Python Workshop",
  "date": "2026-10-14",
  "recipients": [
    {
      "name": "Rahul Sharma",
      "email": "rahul.sharma@example.com"
    },
    {
      "name": "Priya Patel",
      "email": "priya.patel@example.com"
    }
  ]
}
```

**Response (`201 Created`):**
```json
{
  "job_id": 1,
  "status": "completed",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "event_name": "Full Stack Python Workshop",
  "event_date": "2026-10-14",
  "created_at": "2026-10-14T10:48:00.123456Z",
  "certificates": [
    {
      "id": 1,
      "recipient_name": "Rahul Sharma",
      "email": "rahul.sharma@example.com",
      "status": "success",
      "error": null,
      "download_url": "/certificates/1"
    },
    {
      "id": 2,
      "recipient_name": "Priya Patel",
      "email": "priya.patel@example.com",
      "status": "success",
      "error": null,
      "download_url": "/certificates/2"
    }
  ]
}
```

---

### 2. Check Job Status & Summary

`GET /jobs/{job_id}`

Retrieves overall job status, progress statistics, and metadata for all recipients in the job.

---

### 3. List All Certificates for a Job

`GET /jobs/{job_id}/certificates`

Returns the complete array of certificate items generated for this specific batch.

---

### 4. Download Certificate PDF

`GET /certificates/{certificate_id}`

Downloads the generated PDF certificate (`application/pdf`) as an attachment.
- Returns `200 OK` with binary PDF.
- Returns `404 Not Found` if the certificate ID does not exist or the file is missing from disk.

---

### 5. Check Individual Certificate Status

`GET /certificates/{certificate_id}/status`

Retrieves certificate generation details without downloading the binary payload:
```json
{
  "id": 1,
  "recipient_name": "Rahul Sharma",
  "email": "rahul.sharma@example.com",
  "status": "success",
  "error": null,
  "download_url": "/certificates/1"
}
```

---

## Running Tests

The test suite runs with Pytest and validates input validation, database operations, 404 handlers, PDF header signatures, failure isolation, and missing file edge cases.

From either the repository root or project directory:
```bash
pytest -v
```

---

## License

This project is open-source and available under the [MIT License](LICENSE).
