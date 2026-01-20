from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ProgramStudi, JalurMasuk
from app.schemas import ProgramStudiCreate, ProgramStudiResponse, JalurMasukCreate, JalurMasukResponse

router = APIRouter(prefix="/api/master", tags=["Master Data"])


# Program Studi Endpoints
@router.post("/program-studi", response_model=ProgramStudiResponse, status_code=status.HTTP_201_CREATED)
async def create_program_studi(data: ProgramStudiCreate, db: Session = Depends(get_db)):
    """Create new program studi"""
    
    # Check if kode already exists
    existing = db.query(ProgramStudi).filter_by(kode=data.kode).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Kode program studi '{data.kode}' sudah ada"
        )
    
    program_studi = ProgramStudi(
        kode=data.kode,
        nama=data.nama,
        fakultas=data.fakultas
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    return program_studi


@router.get("/program-studi", response_model=list[ProgramStudiResponse])
async def list_program_studi(db: Session = Depends(get_db)):
    """Get all program studi"""
    return db.query(ProgramStudi).all()


@router.get("/program-studi/{studi_id}", response_model=ProgramStudiResponse)
async def get_program_studi(studi_id: int, db: Session = Depends(get_db)):
    """Get program studi by ID"""
    program_studi = db.query(ProgramStudi).filter_by(id=studi_id).first()
    if not program_studi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program studi dengan ID {studi_id} tidak ditemukan"
        )
    return program_studi


# Jalur Masuk Endpoints
@router.post("/jalur-masuk", response_model=JalurMasukResponse, status_code=status.HTTP_201_CREATED)
async def create_jalur_masuk(data: JalurMasukCreate, db: Session = Depends(get_db)):
    """Create new jalur masuk"""
    
    # Check if kode already exists
    existing = db.query(JalurMasuk).filter_by(kode=data.kode).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Kode jalur masuk '{data.kode}' sudah ada"
        )
    
    jalur = JalurMasuk(
        kode=data.kode,
        nama=data.nama,
        deskripsi=data.deskripsi
    )
    db.add(jalur)
    db.commit()
    db.refresh(jalur)
    return jalur


@router.get("/jalur-masuk", response_model=list[JalurMasukResponse])
async def list_jalur_masuk(db: Session = Depends(get_db)):
    """Get all jalur masuk"""
    return db.query(JalurMasuk).all()


@router.get("/jalur-masuk/{jalur_id}", response_model=JalurMasukResponse)
async def get_jalur_masuk(jalur_id: int, db: Session = Depends(get_db)):
    """Get jalur masuk by ID"""
    jalur = db.query(JalurMasuk).filter_by(id=jalur_id).first()
    if not jalur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jalur masuk dengan ID {jalur_id} tidak ditemukan"
        )
    return jalur
