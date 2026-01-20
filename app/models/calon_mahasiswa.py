from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Date, func
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class StatusPendaftaran(str, PyEnum):
    """Enum untuk status pendaftaran"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CalonMahasiswa(Base):
    """Model untuk data calon mahasiswa"""
    
    __tablename__ = "calon_mahasiswa"
    
    id = Column(Integer, primary_key=True, index=True)
    nama_lengkap = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    tanggal_lahir = Column(Date, nullable=False)
    alamat = Column(String(255), nullable=False)
    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False, index=True)
    jalur_masuk_id = Column(Integer, ForeignKey("jalur_masuk.id"), nullable=False, index=True)
    status = Column(Enum(StatusPendaftaran), default=StatusPendaftaran.PENDING, nullable=False, index=True)
    nim = Column(String(20), unique=True, nullable=True, index=True)  # NIM generated after approval
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    approved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    program_studi = relationship("ProgramStudi")
    jalur_masuk = relationship("JalurMasuk")
    
    def __repr__(self):
        return f"<CalonMahasiswa(id={self.id}, nama={self.nama_lengkap}, email={self.email}, nim={self.nim})>"
