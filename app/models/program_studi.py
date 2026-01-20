from sqlalchemy import Column, Integer, String, DateTime, func
from datetime import datetime
from app.database import Base


class ProgramStudi(Base):
    """Model untuk data program studi"""
    
    __tablename__ = "program_studi"
    
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(3), unique=True, nullable=False, index=True)  # 3 char code
    nama = Column(String(100), nullable=False)
    fakultas = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ProgramStudi(id={self.id}, kode={self.kode}, nama={self.nama})>"
