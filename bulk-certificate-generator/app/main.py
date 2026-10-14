from pathlib import Path
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import Job, Certificate
from .schemas import GenerationRequest, JobResponse, CertificateResponse
from .services import generate_certificate

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="API for bulk generating PDF certificates, tracking job status, and retrieving certificates.",
    version="1.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _build_job_response(job: Job) -> JobResponse:
    cert_list = [
        CertificateResponse(
            id=cert.id,
            recipient_name=cert.recipient_name,
            email=cert.email,
            status=cert.status,
            error=cert.error,
            download_url=f"/certificates/{cert.id}" if cert.status == "success" else None
        )
        for cert in (job.certificates or [])
    ]
    return JobResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed,
        event_name=job.event_name,
        event_date=job.event_date,
        created_at=job.created_at,
        certificates=cert_list
    )

@app.get("/")
def root():
    return {"message": "Bulk Certificate Generator API is running"}

@app.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(request: GenerationRequest, db: Session = Depends(get_db)):
    job = Job(
        event_name=request.event_name,
        event_date=request.date,
        total=len(request.recipients),
        successful=0,
        failed=0,
        status="processing"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        for recipient in request.recipients:
            cert = Certificate(
                job_id=job.id,
                recipient_name=recipient.name,
                email=str(recipient.email),
                status="processing"
            )
            db.add(cert)
            db.commit()
            db.refresh(cert)

            try:
                cert.file_path = generate_certificate(
                    request.event_name, request.date, recipient.name, cert.id
                )
                cert.status = "success"
                job.successful += 1
            except Exception as exc:
                cert.status = "failed"
                cert.error = str(exc)
                job.failed += 1

            db.commit()

        job.status = "completed"
        db.commit()
        db.refresh(job)
    except Exception as exc:
        db.rollback()
        job.status = "failed"
        try:
            db.commit()
            db.refresh(job)
        except Exception:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Job processing error: {str(exc)}")

    return _build_job_response(job)

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _build_job_response(job)

@app.get("/jobs/{job_id}/certificates", response_model=List[CertificateResponse])
def get_job_certificates(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return [
        CertificateResponse(
            id=cert.id,
            recipient_name=cert.recipient_name,
            email=cert.email,
            status=cert.status,
            error=cert.error,
            download_url=f"/certificates/{cert.id}" if cert.status == "success" else None
        )
        for cert in job.certificates
    ]

@app.get("/certificates/{certificate_id}")
def get_certificate(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != "success" or not cert.file_path:
        raise HTTPException(status_code=404, detail="Certificate was not generated")
    
    file_path = Path(cert.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Certificate file not found on disk")

    return FileResponse(
        str(file_path),
        media_type="application/pdf",
        filename=f"certificate_{certificate_id}.pdf"
    )

@app.get("/certificates/{certificate_id}/status", response_model=CertificateResponse)
def get_certificate_status(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return CertificateResponse(
        id=cert.id,
        recipient_name=cert.recipient_name,
        email=cert.email,
        status=cert.status,
        error=cert.error,
        download_url=f"/certificates/{cert.id}" if cert.status == "success" else None
    )

