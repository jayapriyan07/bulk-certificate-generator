from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import Job, Certificate
from .schemas import GenerationRequest, JobResponse
from .services import generate_certificate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Bulk Certificate Generator API is running"}

@app.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(request: GenerationRequest, db: Session = Depends(get_db)):
    job = Job(
        event_name=request.event_name,
        event_date=request.date,
        total=len(request.recipients),
        status="processing"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

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

    return JobResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed
    )

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed
    )

@app.get("/certificates/{certificate_id}")
def get_certificate(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != "success" or not cert.file_path:
        raise HTTPException(status_code=404, detail="Certificate was not generated")
    return FileResponse(
        cert.file_path,
        media_type="application/pdf",
        filename=f"certificate_{certificate_id}.pdf"
    )
