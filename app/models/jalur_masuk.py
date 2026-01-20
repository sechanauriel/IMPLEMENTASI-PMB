from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class JalurMasuk(Base):
    """Model untuk jalur masuk (SNBP, SNBT, Mandiri)"""
    
    __tablename__ = "jalur_masuk"
    
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(20), unique=True, nullable=False, index=True)  # SNBP, SNBT, Mandiri
    nama = Column(String(100), nullable=False)
    deskripsi = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<JalurMasuk(id={self.id}, kode={self.kode}, nama={self.nama})>"
