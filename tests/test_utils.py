import pytest
from datetime import date
from app.utils.nim_generator import generate_nim, validate_nim_format, parse_nim
from app.utils.validators import (
    validate_email,
    validate_phone_indonesia,
    normalize_phone
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import ProgramStudi, CalonMahasiswa

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_utils.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_with_prodi():
    """Setup database dengan program studi"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    prodi = ProgramStudi(kode="001", nama="TI", fakultas="Teknik")
    db.add(prodi)
    db.commit()
    db.refresh(prodi)
    
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# ================== NIM GENERATOR TESTS ==================

class TestNIMGenerator:
    """Test NIM generator utility"""
    
    def test_generate_nim_format(self, db_with_prodi):
        """Test generate NIM dengan format yang benar"""
        prodi = db_with_prodi.query(ProgramStudi).first()
        
        calon = CalonMahasiswa(
            nama_lengkap="Test",
            email="test@email.com",
            phone="+628123456789",
            tanggal_lahir=date(2005, 1, 15),
            alamat="Test",
            program_studi_id=prodi.id,
            jalur_masuk_id=1,
            status="pending"
        )
        db_with_prodi.add(calon)
        db_with_prodi.commit()
        db_with_prodi.refresh(calon)
        
        nim = generate_nim(calon.id, 2025, "001", db_with_prodi)
        
        # Format: YYYY001-XXXX
        assert validate_nim_format(nim)
        assert nim.startswith("2025001-")
    
    def test_generate_nim_idempotent(self, db_with_prodi):
        """Test generate NIM idempotent"""
        prodi = db_with_prodi.query(ProgramStudi).first()
        
        calon = CalonMahasiswa(
            nama_lengkap="Test",
            email="test@email.com",
            phone="+628123456789",
            tanggal_lahir=date(2005, 1, 15),
            alamat="Test",
            program_studi_id=prodi.id,
            jalur_masuk_id=1,
            status="pending"
        )
        db_with_prodi.add(calon)
        db_with_prodi.commit()
        db_with_prodi.refresh(calon)
        
        # Generate twice
        nim1 = generate_nim(calon.id, 2025, "001", db_with_prodi)
        nim2 = generate_nim(calon.id, 2025, "001", db_with_prodi)
        
        # Should return same NIM (idempotent)
        assert nim1 == nim2
    
    def test_generate_nim_sequential(self, db_with_prodi):
        """Test generate NIM sequential"""
        prodi = db_with_prodi.query(ProgramStudi).first()
        
        nims = []
        for i in range(3):
            calon = CalonMahasiswa(
                nama_lengkap=f"Test {i}",
                email=f"test{i}@email.com",
                phone=f"+628123456789{i}",
                tanggal_lahir=date(2005, 1, 15),
                alamat="Test",
                program_studi_id=prodi.id,
                jalur_masuk_id=1,
                status="pending"
            )
            db_with_prodi.add(calon)
            db_with_prodi.commit()
            db_with_prodi.refresh(calon)
            
            nim = generate_nim(calon.id, 2025, "001", db_with_prodi)
            nims.append(nim)
        
        # Check sequential
        assert nims[0][-4:] == "0001"
        assert nims[1][-4:] == "0002"
        assert nims[2][-4:] == "0003"
    
    def test_generate_nim_invalid_tahun(self, db_with_prodi):
        """Test generate NIM dengan tahun tidak valid"""
        prodi = db_with_prodi.query(ProgramStudi).first()
        
        calon = CalonMahasiswa(
            nama_lengkap="Test",
            email="test@email.com",
            phone="+628123456789",
            tanggal_lahir=date(2005, 1, 15),
            alamat="Test",
            program_studi_id=prodi.id,
            jalur_masuk_id=1,
            status="pending"
        )
        db_with_prodi.add(calon)
        db_with_prodi.commit()
        db_with_prodi.refresh(calon)
        
        with pytest.raises(ValueError):
            generate_nim(calon.id, 1999, "001", db_with_prodi)
    
    def test_generate_nim_invalid_kode_prodi(self, db_with_prodi):
        """Test generate NIM dengan kode prodi tidak valid"""
        prodi = db_with_prodi.query(ProgramStudi).first()
        
        calon = CalonMahasiswa(
            nama_lengkap="Test",
            email="test@email.com",
            phone="+628123456789",
            tanggal_lahir=date(2005, 1, 15),
            alamat="Test",
            program_studi_id=prodi.id,
            jalur_masuk_id=1,
            status="pending"
        )
        db_with_prodi.add(calon)
        db_with_prodi.commit()
        db_with_prodi.refresh(calon)
        
        # Should not be 3 digits
        with pytest.raises(ValueError):
            generate_nim(calon.id, 2025, "01", db_with_prodi)
        
        # Should be numeric
        with pytest.raises(ValueError):
            generate_nim(calon.id, 2025, "00A", db_with_prodi)
    
    def test_validate_nim_format_valid(self):
        """Test validate NIM format dengan format valid"""
        assert validate_nim_format("2025001-0001")
        assert validate_nim_format("2025999-9999")
        assert validate_nim_format("2000001-0001")
    
    def test_validate_nim_format_invalid(self):
        """Test validate NIM format dengan format tidak valid"""
        assert not validate_nim_format("2025-001-0001")  # Wrong separator
        assert not validate_nim_format("20250010001")     # No separator
        assert not validate_nim_format("2025001")         # Missing number
        assert not validate_nim_format("ABC0001-0001")    # Non-numeric tahun
    
    def test_parse_nim_valid(self):
        """Test parse NIM dengan format valid"""
        parsed = parse_nim("2025001-0001")
        assert parsed["tahun"] == 2025
        assert parsed["kode_prodi"] == "001"
        assert parsed["running_number"] == 1
    
    def test_parse_nim_invalid(self):
        """Test parse NIM dengan format tidak valid"""
        with pytest.raises(ValueError):
            parse_nim("invalid-nim")


# ================== VALIDATOR TESTS ==================

class TestValidators:
    """Test validation utilities"""
    
    def test_validate_email_valid(self):
        """Test validate email dengan format valid"""
        assert validate_email("test@example.com")
        assert validate_email("user.name@domain.co.id")
        assert validate_email("admin+tag@company.com")
    
    def test_validate_email_invalid(self):
        """Test validate email dengan format tidak valid"""
        assert not validate_email("invalid.email")
        assert not validate_email("user@.com")
        assert not validate_email("@example.com")
    
    def test_validate_phone_indonesia_valid(self):
        """Test validate nomor Indonesia dengan format valid"""
        assert validate_phone_indonesia("082123456789")
        assert validate_phone_indonesia("081234567890")
        assert validate_phone_indonesia("+628123456789")
        assert validate_phone_indonesia("+62812345678")
    
    def test_validate_phone_indonesia_invalid(self):
        """Test validate nomor Indonesia dengan format tidak valid"""
        assert not validate_phone_indonesia("123456789")
        assert not validate_phone_indonesia("6281234567890")  # Missing +
        assert not validate_phone_indonesia("+1234567890")
        assert not validate_phone_indonesia("08-1234-5678")   # With separator
    
    def test_normalize_phone_with_0(self):
        """Test normalize nomor yang dimulai dengan 0"""
        result = normalize_phone("081234567890")
        assert result == "+6281234567890"
    
    def test_normalize_phone_with_62(self):
        """Test normalize nomor yang dimulai dengan 62"""
        result = normalize_phone("6281234567890")
        assert result == "+6281234567890"
    
    def test_normalize_phone_with_plus62(self):
        """Test normalize nomor yang dimulai dengan +62"""
        result = normalize_phone("+6281234567890")
        assert result == "+6281234567890"
    
    def test_normalize_phone_invalid(self):
        """Test normalize nomor dengan format tidak valid"""
        with pytest.raises(ValueError):
            normalize_phone("123456789")
