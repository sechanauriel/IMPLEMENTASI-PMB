from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
import re


class ProgramStudiBase(BaseModel):
    """Base schema untuk program studi"""
    kode: str
    nama: str
    fakultas: str


class ProgramStudiCreate(ProgramStudiBase):
    """Schema untuk create program studi"""
    pass


class ProgramStudiResponse(ProgramStudiBase):
    """Response schema untuk program studi"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JalurMasukBase(BaseModel):
    """Base schema untuk jalur masuk"""
    kode: str
    nama: str
    deskripsi: Optional[str] = None


class JalurMasukCreate(JalurMasukBase):
    """Schema untuk create jalur masuk"""
    pass


class JalurMasukResponse(JalurMasukBase):
    """Response schema untuk jalur masuk"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CalonMahasiswaBase(BaseModel):
    """Base schema untuk calon mahasiswa"""
    nama_lengkap: str
    email: EmailStr
    phone: str
    tanggal_lahir: date
    alamat: str
    program_studi_id: int
    jalur_masuk_id: int
    
    @field_validator('nama_lengkap')
    @classmethod
    def validate_nama(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Nama harus minimal 3 karakter')
        return v.strip()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Indonesian phone validation
        phone_pattern = r'^(\+62|0)[0-9]{9,12}$'
        if not re.match(phone_pattern, v):
            raise ValueError('Format nomor telepon tidak valid (gunakan format Indonesia)')
        return v
    
    @field_validator('alamat')
    @classmethod
    def validate_alamat(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Alamat harus minimal 5 karakter')
        return v.strip()


class CalonMahasiswaCreate(CalonMahasiswaBase):
    """Schema untuk create calon mahasiswa"""
    pass


class CalonMahasiswaUpdate(BaseModel):
    """Schema untuk update calon mahasiswa"""
    nama_lengkap: Optional[str] = None
    phone: Optional[str] = None
    alamat: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        phone_pattern = r'^(\+62|0)[0-9]{9,12}$'
        if not re.match(phone_pattern, v):
            raise ValueError('Format nomor telepon tidak valid (gunakan format Indonesia)')
        return v


class CalonMahasiswaResponse(CalonMahasiswaBase):
    """Response schema untuk calon mahasiswa"""
    id: int
    status: str
    nim: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    updated_at: datetime
    program_studi: ProgramStudiResponse
    jalur_masuk: JalurMasukResponse
    
    class Config:
        from_attributes = True


class CalonMahasiswaListResponse(BaseModel):
    """Response schema untuk list calon mahasiswa"""
    id: int
    nama_lengkap: str
    email: str
    status: str
    nim: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    """Request schema untuk approve calon mahasiswa"""
    pass


class NIMResponse(BaseModel):
    """Response schema untuk NIM"""
    id: int
    nim: str
    nama_lengkap: str
    email: str
    program_studi: str
    status: str


class StatsResponse(BaseModel):
    """Response schema untuk statistik"""
    total_pendaftar: int
    pending: int
    approved: int
    rejected: int
    program_studi_counts: dict  # {program_name: count}
    jalur_masuk_counts: dict    # {jalur_name: count}
