"""
NIM (Nomor Induk Mahasiswa) Generator

Format: YYYY[KODE_PRODI][SEQUENTIAL]
Example: 2025001-0001 (Tahun 2025, Prodi 001 = Teknik Informatika, Pendaftar ke-1)

Thread-safe implementation with database locking to prevent race conditions.
Idempotent - akan return NIM yang sama jika sudah di-generate sebelumnya.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import CalonMahasiswa
import threading

# Lock untuk thread safety
_nim_lock = threading.Lock()


def generate_nim(calon_id: int, tahun: int, kode_prodi: str, db: Session) -> str:
    """
    Generate NIM dengan format: YYYY[KODE]XXXX
    
    Args:
        calon_id: ID calon mahasiswa
        tahun: Tahun pendaftaran (e.g., 2025)
        kode_prodi: Kode program studi (3 karakter, e.g., '001')
        db: Database session
    
    Returns:
        NIM string dengan format YYYY[KODE]XXXX (e.g., '2025001-0001')
    
    Raises:
        ValueError: Jika parameter tidak valid
    """
    
    with _nim_lock:
        # Validasi input
        if not isinstance(tahun, int) or tahun < 2000 or tahun > 2100:
            raise ValueError(f"Tahun tidak valid: {tahun}")
        
        if not isinstance(kode_prodi, str) or len(kode_prodi) != 3 or not kode_prodi.isdigit():
            raise ValueError(f"Kode prodi harus 3 digit: {kode_prodi}")
        
        # Check: Apakah calon ini sudah punya NIM? (idempotent)
        calon = db.query(CalonMahasiswa).filter_by(id=calon_id).first()
        if not calon:
            raise ValueError(f"Calon mahasiswa dengan ID {calon_id} tidak ditemukan")
        
        if calon.nim:
            # Sudah punya NIM, return yang sudah ada (idempotent)
            return calon.nim
        
        # Hitung running number: berapa banyak NIM sudah di-generate untuk tahun+prodi ini?
        existing_count = db.query(func.count(CalonMahasiswa.id)).filter(
            and_(
                CalonMahasiswa.nim.isnot(None),
                CalonMahasiswa.nim.like(f"{tahun}{kode_prodi}%")
            )
        ).scalar()
        
        # Running number dimulai dari 0001
        running_number = existing_count + 1
        
        # Format: YYYY-KODE-XXXX atau YYYY[KODE]XXXX
        nim = f"{tahun}{kode_prodi}-{running_number:04d}"
        
        # Simpan NIM ke database
        calon.nim = nim
        db.add(calon)
        db.commit()
        db.refresh(calon)
        
        return nim


def validate_nim_format(nim: str) -> bool:
    """
    Validasi format NIM
    
    Args:
        nim: NIM string
    
    Returns:
        True jika format valid, False sebaliknya
    """
    import re
    # Format: YYYY[3digit]-XXXX
    pattern = r'^\d{4}\d{3}-\d{4}$'
    return bool(re.match(pattern, nim))


def parse_nim(nim: str) -> dict:
    """
    Parse NIM menjadi komponennya
    
    Args:
        nim: NIM string (e.g., '2025001-0001')
    
    Returns:
        Dictionary dengan keys: tahun, kode_prodi, running_number
    
    Raises:
        ValueError: Jika format NIM tidak valid
    """
    if not validate_nim_format(nim):
        raise ValueError(f"Format NIM tidak valid: {nim}")
    
    tahun = int(nim[:4])
    kode_prodi = nim[4:7]
    running_number = int(nim[8:])
    
    return {
        'tahun': tahun,
        'kode_prodi': kode_prodi,
        'running_number': running_number
    }
