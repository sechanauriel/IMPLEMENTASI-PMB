from datetime import datetime, timezone
import re
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, validates

Base = declarative_base()

# Regex for email (simple but practical)
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
# Regex for Indonesian phone numbers: start +62 or 62 or 0, then 8..., reasonable length 9-15
PHONE_REGEX = r"^(?:\+62|62|0)8[1-9][0-9]{6,10}$"

# Enum options
JALUR_MASUK_OPTIONS = ("SNBP", "SNBT", "Mandiri")
STATUS_OPTIONS = ("pending", "approved", "rejected")

# No top-level engine/session here — application config provides DB engine.

class ProgramStudi(Base):
    __tablename__ = "program_studi"

    id = Column(Integer, primary_key=True)
    kode = Column(String(3), nullable=False, unique=True, index=True)
    nama = Column(String(255), nullable=False)
    fakultas = Column(String(255), nullable=False)

    calon_mahasiswa = relationship("CalonMahasiswa", back_populates="program_studi")

    def __repr__(self) -> str:
        return f"<ProgramStudi(id={self.id}, kode={self.kode}, nama={self.nama})>"


class CalonMahasiswa(Base):
    __tablename__ = "calon_mahasiswa"

    id = Column(Integer, primary_key=True)
    nama_lengkap = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(32), nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    alamat = Column(String(1024), nullable=True)

    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False)
    program_studi = relationship("ProgramStudi", back_populates="calon_mahasiswa")

    jalur_masuk = Column(Enum(*JALUR_MASUK_OPTIONS, name="jalur_masuk_enum"), nullable=False)
    status = Column(Enum(*STATUS_OPTIONS, name="status_enum"), default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    nim = Column(String(32), nullable=True, unique=True, index=True)

    # Note: regex CHECK constraints are applied in Alembic migrations for Postgres.
    __table_args__ = ()

    def __repr__(self) -> str:
        return f"<CalonMahasiswa(id={self.id}, nama={self.nama_lengkap}, email={self.email})>"

    # Python-level validation to provide nicer error messages earlier
    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        if not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        return value

    @validates("phone")
    def validate_phone(self, key: str, value: str) -> str:
        # Basic normalization: remove spaces
        val = value.strip()
        if not re.match(PHONE_REGEX, val):
            raise ValueError("Invalid Indonesian phone number format (expect +62/62/0 followed by 8...)")
        return val

    def generate_nim(self):
        """Generate NIM placeholder. Real generation is done in the endpoint to ensure uniqueness.

        Format: [tahun][kode_prodi][sequential] where sequential is a zero-padded 4-digit number.
        Returns a string NIM without persisting it.
        """
        if not getattr(self, "program_studi", None):
            raise ValueError("Program studi must be set for NIM generation")
        year = datetime.now(timezone.utc).year
        kode = self.program_studi.kode
        # Placeholder for sequential; real code in endpoint ensures unique sequential number
        return f"{year}{kode}0001"


class NIMCounter(Base):
    __tablename__ = "nim_counters"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    kode_prodi = Column(String(10), nullable=False)
    last_seq = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('year', 'kode_prodi', name='uq_nimcounter_year_kode'),
    )

    def __repr__(self) -> str:
        return f"<NIMCounter(year={self.year}, kode_prodi={self.kode_prodi}, last_seq={self.last_seq})>"

# models only — no runtime/demo DB operations here
