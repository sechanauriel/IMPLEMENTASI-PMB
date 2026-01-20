from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.models import CalonMahasiswa, ProgramStudi, JalurMasuk, StatusPendaftaran
from app.schemas import (
    CalonMahasiswaCreate, 
    CalonMahasiswaResponse,
    CalonMahasiswaListResponse,
    ApproveRequest,
    NIMResponse,
    StatsResponse
)
from app.utils.nim_generator import generate_nim, validate_nim_format
from app.utils.validators import validate_phone_indonesia, normalize_phone

router = APIRouter(prefix="/api/pmb", tags=["PMB"])


@router.post("/register", response_model=CalonMahasiswaResponse, status_code=status.HTTP_201_CREATED)
async def register_calon_mahasiswa(
    data: CalonMahasiswaCreate,
    db: Session = Depends(get_db)
):
    """
    Register calon mahasiswa baru
    
    Validasi:
    - Email harus unik
    - Nomor telepon format Indonesia
    - Program studi dan jalur masuk harus valid
    """
    
    # Check: Email sudah terdaftar?
    existing_email = db.query(CalonMahasiswa).filter_by(email=data.email.lower()).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar. Gunakan email lain."
        )
    
    # Check: Program studi valid?
    program_studi = db.query(ProgramStudi).filter_by(id=data.program_studi_id).first()
    if not program_studi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Program studi dengan ID {data.program_studi_id} tidak ditemukan"
        )
    
    # Check: Jalur masuk valid?
    jalur_masuk = db.query(JalurMasuk).filter_by(id=data.jalur_masuk_id).first()
    if not jalur_masuk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Jalur masuk dengan ID {data.jalur_masuk_id} tidak ditemukan"
        )
    
    # Validate phone format
    if not validate_phone_indonesia(data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format nomor telepon tidak valid. Gunakan format Indonesia (0812... atau +628...)"
        )
    
    # Create new calon mahasiswa
    calon = CalonMahasiswa(
        nama_lengkap=data.nama_lengkap,
        email=data.email.lower(),
        phone=normalize_phone(data.phone),
        tanggal_lahir=data.tanggal_lahir,
        alamat=data.alamat,
        program_studi_id=data.program_studi_id,
        jalur_masuk_id=data.jalur_masuk_id,
        status=StatusPendaftaran.PENDING
    )
    
    db.add(calon)
    db.commit()
    db.refresh(calon)
    
    return calon


@router.get("/status/{calon_id}", response_model=CalonMahasiswaResponse)
async def get_registration_status(
    calon_id: int,
    db: Session = Depends(get_db)
):
    """
    Cek status pendaftaran calon mahasiswa
    """
    
    calon = db.query(CalonMahasiswa).filter_by(id=calon_id).first()
    if not calon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calon mahasiswa dengan ID {calon_id} tidak ditemukan"
        )
    
    return calon


@router.put("/approve/{calon_id}", response_model=NIMResponse, status_code=status.HTTP_200_OK)
async def approve_calon_mahasiswa(
    calon_id: int,
    request: ApproveRequest,
    db: Session = Depends(get_db)
):
    """
    Admin approve calon mahasiswa dan generate NIM otomatis
    
    Format NIM: YYYY[KODE_PRODI][RUNNING_NUMBER]
    Contoh: 2025001-0001
    
    Idempotent: Jika sudah approve, tidak generate NIM baru
    """
    
    calon = db.query(CalonMahasiswa).filter_by(id=calon_id).first()
    if not calon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calon mahasiswa dengan ID {calon_id} tidak ditemukan"
        )
    
    # Jika sudah approve dan punya NIM, return yang existing (idempotent)
    if calon.status == StatusPendaftaran.APPROVED and calon.nim:
        return NIMResponse(
            id=calon.id,
            nim=calon.nim,
            nama_lengkap=calon.nama_lengkap,
            email=calon.email,
            program_studi=calon.program_studi.nama,
            status=calon.status.value
        )
    
    # Generate NIM
    tahun_pendaftaran = datetime.now().year
    kode_prodi = calon.program_studi.kode
    
    try:
        nim = generate_nim(calon.id, tahun_pendaftaran, kode_prodi, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal generate NIM: {str(e)}"
        )
    
    # Update calon status menjadi approved dan set NIM
    calon.status = StatusPendaftaran.APPROVED
    calon.nim = nim
    calon.approved_at = datetime.utcnow()
    calon.updated_at = datetime.utcnow()
    
    db.add(calon)
    db.commit()
    db.refresh(calon)
    
    return NIMResponse(
        id=calon.id,
        nim=calon.nim,
        nama_lengkap=calon.nama_lengkap,
        email=calon.email,
        program_studi=calon.program_studi.nama,
        status=calon.status.value
    )


@router.get("/list", response_model=list[CalonMahasiswaListResponse])
async def list_calon_mahasiswa(
    status_filter: str = Query(None, description="Filter by status: pending, approved, rejected"),
    program_studi_id: int = Query(None, description="Filter by program studi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Dapatkan list calon mahasiswa dengan filter dan pagination
    """
    
    query = db.query(CalonMahasiswa)
    
    # Apply filters
    if status_filter:
        try:
            status_enum = StatusPendaftaran(status_filter.lower())
            query = query.filter_by(status=status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status tidak valid. Gunakan: pending, approved, rejected"
            )
    
    if program_studi_id:
        query = query.filter_by(program_studi_id=program_studi_id)
    
    # Order by created_at descending dan apply pagination
    calon_list = query.order_by(CalonMahasiswa.created_at.desc()).offset(skip).limit(limit).all()
    
    return calon_list


@router.get("/stats", response_model=StatsResponse)
async def get_pmb_statistics(db: Session = Depends(get_db)):
    """
    Dapatkan statistik PMB (dashboard)
    """
    
    # Total pendaftar
    total_pendaftar = db.query(func.count(CalonMahasiswa.id)).scalar() or 0
    
    # Count by status
    pending_count = db.query(func.count(CalonMahasiswa.id)).filter_by(
        status=StatusPendaftaran.PENDING
    ).scalar() or 0
    
    approved_count = db.query(func.count(CalonMahasiswa.id)).filter_by(
        status=StatusPendaftaran.APPROVED
    ).scalar() or 0
    
    rejected_count = db.query(func.count(CalonMahasiswa.id)).filter_by(
        status=StatusPendaftaran.REJECTED
    ).scalar() or 0
    
    # Count by program studi
    program_studi_counts_raw = db.query(
        ProgramStudi.nama,
        func.count(CalonMahasiswa.id).label('count')
    ).join(CalonMahasiswa).group_by(ProgramStudi.nama).all()
    
    program_studi_counts = {nama: count for nama, count in program_studi_counts_raw}
    
    # Count by jalur masuk
    jalur_masuk_counts_raw = db.query(
        JalurMasuk.nama,
        func.count(CalonMahasiswa.id).label('count')
    ).join(CalonMahasiswa).group_by(JalurMasuk.nama).all()
    
    jalur_masuk_counts = {nama: count for nama, count in jalur_masuk_counts_raw}
    
    return StatsResponse(
        total_pendaftar=total_pendaftar,
        pending=pending_count,
        approved=approved_count,
        rejected=rejected_count,
        program_studi_counts=program_studi_counts,
        jalur_masuk_counts=jalur_masuk_counts
    )


@router.post("/reject/{calon_id}", status_code=status.HTTP_200_OK)
async def reject_calon_mahasiswa(
    calon_id: int,
    db: Session = Depends(get_db)
):
    """
    Admin reject calon mahasiswa
    """
    
    calon = db.query(CalonMahasiswa).filter_by(id=calon_id).first()
    if not calon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calon mahasiswa dengan ID {calon_id} tidak ditemukan"
        )
    
    calon.status = StatusPendaftaran.REJECTED
    calon.updated_at = datetime.utcnow()
    
    db.add(calon)
    db.commit()
    db.refresh(calon)
    
    return {"message": "Calon mahasiswa berhasil di-reject", "id": calon.id}
