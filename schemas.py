from datetime import date, datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, field_validator, StringConstraints, ConfigDict
import re

PHONE_REGEX = r"^(?:\+62|62|0)8[1-9][0-9]{6,10}$"


class ProgramStudiBase(BaseModel):
    kode: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    nama: str
    fakultas: str


class ProgramStudiCreate(ProgramStudiBase):
    pass


class ProgramStudiOut(ProgramStudiBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CalonMahasiswaBase(BaseModel):
    nama_lengkap: str
    email: EmailStr
    phone: Annotated[str, StringConstraints(min_length=8, max_length=32)]
    tanggal_lahir: date
    alamat: Optional[str] = None
    program_studi_id: int
    jalur_masuk: str

    @field_validator('jalur_masuk')
    @classmethod
    def validate_jalur(cls, v: str) -> str:
        allowed = ('SNBP', 'SNBT', 'Mandiri')
        if v not in allowed:
            raise ValueError('Invalid jalur_masuk, expected one of: ' + ','.join(allowed))
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(PHONE_REGEX, v):
            raise ValueError('Invalid Indonesian phone number format')
        return v


class CalonMahasiswaCreate(CalonMahasiswaBase):
    pass


class CalonMahasiswaOut(CalonMahasiswaBase):
    id: int
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    nim: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
