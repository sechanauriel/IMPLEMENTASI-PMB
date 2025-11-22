from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Any, cast
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from models import Base, ProgramStudi, CalonMahasiswa
from schemas import CalonMahasiswaCreate, CalonMahasiswaOut
from database import engine, get_db

from sqlalchemy.exc import IntegrityError

# Create DB metadata for sqlite quickstart (in case)
Base.metadata.create_all(bind=engine)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    print("✓ Application shutdown")


app = FastAPI(title="PMB API", lifespan=lifespan)

# Serve static files from the `static/` directory at the `/static` path
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/register", response_model=CalonMahasiswaOut, status_code=status.HTTP_201_CREATED)
def register_mahasiswa(payload: CalonMahasiswaCreate, db: Session = Depends(get_db)):
    # Check program studi exists
    program = db.query(ProgramStudi).filter(ProgramStudi.id == payload.program_studi_id).first()
    if not program:
        raise HTTPException(status_code=400, detail=f"program_studi_id {payload.program_studi_id} not found")

    # Check for email conflict
    exists = db.query(CalonMahasiswa).filter(func.lower(CalonMahasiswa.email) == payload.email.lower()).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")

    calon = CalonMahasiswa(
        nama_lengkap=payload.nama_lengkap,
        email=payload.email,
        phone=payload.phone,
        tanggal_lahir=payload.tanggal_lahir,
        alamat=payload.alamat,
        program_studi_id=payload.program_studi_id,
        jalur_masuk=payload.jalur_masuk,
        status="pending",
    )

    db.add(calon)
    db.commit()
    db.refresh(calon)
    return calon


@app.put("/approve/{id}")
def approve_mahasiswa(id: int, db: Session = Depends(get_db)):
    calon = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == id).first()
    if not calon:
        raise HTTPException(status_code=404, detail="Calon mahasiswa not found")

    status_val = getattr(calon, "status", None)
    if status_val == "approved":
        return {"nim": calon.nim}
    if status_val != "pending":
        raise HTTPException(status_code=409, detail=f"Cannot approve candidate with status {status_val}")

    # Generate NIM: [tahun][kode_prodi][sequential]
    year = datetime.now(timezone.utc).year
    kode = calon.program_studi.kode
    prefix = f"{year}{kode}"

    # Find highest existing sequential for this prefix
    like_pattern = f"{prefix}%"
    # fetch next sequence
    existing_count = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim.like(like_pattern)).count()

    for attempt in range(5):
        seq = existing_count + 1 + attempt
        nim_candidate = f"{prefix}{seq:04d}"
        # use a mypy-safe cast to assign to SQLAlchemy mapped attributes
        calon_any = cast(Any, calon)
        calon_any.nim = nim_candidate
        calon_any.status = "approved"
        calon_any.approved_at = datetime.now(timezone.utc)
        try:
            db.add(calon)
            db.commit()
            db.refresh(calon)
            return {"nim": calon.nim}
        except IntegrityError:
            db.rollback()
            # If someone else inserted with the same NIM concurrently, try next
            continue

    raise HTTPException(status_code=409, detail="Could not generate unique NIM; please retry")


@app.get("/status/{id}", response_model=CalonMahasiswaOut)
def get_status(id: int, db: Session = Depends(get_db)):
    calon = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == id).first()
    if not calon:
        raise HTTPException(status_code=404, detail="Calon mahasiswa not found")
    return calon


@app.get("/", include_in_schema=False)
def root_redirect():
    # Redirect root to the static landing page (or change to /docs for API docs)
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
