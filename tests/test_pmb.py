import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import ProgramStudi, JalurMasuk, CalonMahasiswa, StatusPendaftaran
from datetime import date, datetime, timedelta

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def setup_master_data(setup_database):
    """Setup master data (program studi dan jalur masuk)"""
    db = TestingSessionLocal()
    
    # Create program studi
    prodi1 = ProgramStudi(kode="001", nama="Teknik Informatika", fakultas="Teknik")
    prodi2 = ProgramStudi(kode="002", nama="Sistem Informasi", fakultas="Teknik")
    prodi3 = ProgramStudi(kode="003", nama="Teknik Komputer", fakultas="Teknik")
    
    db.add_all([prodi1, prodi2, prodi3])
    db.flush()
    
    # Create jalur masuk
    jalur1 = JalurMasuk(kode="SNBP", nama="Seleksi Nasional Berbasis Prestasi")
    jalur2 = JalurMasuk(kode="SNBT", nama="Seleksi Nasional Berbasis Tes")
    jalur3 = JalurMasuk(kode="MANDIRI", nama="Jalur Mandiri")
    
    db.add_all([jalur1, jalur2, jalur3])
    db.commit()
    
    data = {
        "prodi": [prodi1, prodi2, prodi3],
        "jalur": [jalur1, jalur2, jalur3]
    }
    
    db.close()
    return data


# ================== MASTER DATA TESTS ==================

class TestMasterData:
    """Test master data endpoints"""
    
    def test_create_program_studi(self, setup_database):
        """Test create program studi"""
        response = client.post(
            "/api/master/program-studi",
            json={
                "kode": "001",
                "nama": "Teknik Informatika",
                "fakultas": "Teknik"
            }
        )
        assert response.status_code == 201
        assert response.json()["kode"] == "001"
        assert response.json()["nama"] == "Teknik Informatika"
    
    def test_create_program_studi_duplicate_kode(self, setup_database):
        """Test create program studi dengan kode yang sudah ada"""
        client.post(
            "/api/master/program-studi",
            json={"kode": "001", "nama": "TI", "fakultas": "Teknik"}
        )
        response = client.post(
            "/api/master/program-studi",
            json={"kode": "001", "nama": "TI Lain", "fakultas": "Teknik"}
        )
        assert response.status_code == 409
    
    def test_list_program_studi(self, setup_master_data):
        """Test list program studi"""
        response = client.get("/api/master/program-studi")
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_create_jalur_masuk(self, setup_database):
        """Test create jalur masuk"""
        response = client.post(
            "/api/master/jalur-masuk",
            json={
                "kode": "SNBP",
                "nama": "Seleksi Nasional Berbasis Prestasi",
                "deskripsi": "Jalur SNBP"
            }
        )
        assert response.status_code == 201
        assert response.json()["kode"] == "SNBP"
    
    def test_list_jalur_masuk(self, setup_master_data):
        """Test list jalur masuk"""
        response = client.get("/api/master/jalur-masuk")
        assert response.status_code == 200
        assert len(response.json()) >= 1


# ================== PMB REGISTRATION TESTS ==================

class TestPMBRegistration:
    """Test PMB registration endpoints"""
    
    def test_register_success(self, setup_master_data):
        """Test successful registration"""
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad.hidayat@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"
        assert response.json()["email"] == "ahmad.hidayat@email.com"
    
    def test_register_duplicate_email(self, setup_master_data):
        """Test registration dengan email yang sudah terdaftar"""
        # Register first
        client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Budi Santoso",
                "email": "ahmad@email.com",
                "phone": "081234567890",
                "tanggal_lahir": "2005-02-15",
                "alamat": "Jl. Sudirman, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        assert response.status_code == 409
        assert "Email sudah terdaftar" in response.json()["detail"]
    
    def test_register_invalid_email(self, setup_master_data):
        """Test registration dengan email format tidak valid"""
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "invalid-email",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_invalid_phone_format(self, setup_master_data):
        """Test registration dengan nomor telepon format tidak valid"""
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "123456",  # Invalid format
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        assert response.status_code == 422
    
    def test_register_valid_phone_formats(self, setup_master_data):
        """Test registration dengan berbagai format nomor telepon yang valid"""
        valid_phones = [
            "082123456789",      # 0812...
            "+628123456789",     # +6281...
        ]
        
        for idx, phone in enumerate(valid_phones):
            response = client.post(
                "/api/pmb/register",
                json={
                    "nama_lengkap": f"Calon {idx}",
                    "email": f"calon{idx}@email.com",
                    "phone": phone,
                    "tanggal_lahir": "2005-01-15",
                    "alamat": "Jl. Test",
                    "program_studi_id": 1,
                    "jalur_masuk_id": 1
                }
            )
            assert response.status_code == 201
    
    def test_register_invalid_program_studi(self, setup_master_data):
        """Test registration dengan program studi yang tidak ada"""
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 999,  # Not exist
                "jalur_masuk_id": 1
            }
        )
        assert response.status_code == 400
        assert "tidak ditemukan" in response.json()["detail"]
    
    def test_register_invalid_jalur_masuk(self, setup_master_data):
        """Test registration dengan jalur masuk yang tidak ada"""
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 999  # Not exist
            }
        )
        assert response.status_code == 400
    
    def test_register_nama_terlalu_pendek(self, setup_master_data):
        """Test registration dengan nama kurang dari 3 karakter"""
        response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ab",  # Too short
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        assert response.status_code == 422


# ================== PMB APPROVAL TESTS ==================

class TestPMBApproval:
    """Test PMB approval dan NIM generation"""
    
    def test_approve_and_generate_nim_success(self, setup_master_data):
        """Test approve calon mahasiswa dan generate NIM otomatis"""
        # Register first
        reg_response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,  # Kode: 001
                "jalur_masuk_id": 1
            }
        )
        calon_id = reg_response.json()["id"]
        
        # Approve
        approve_response = client.put(
            f"/api/pmb/approve/{calon_id}",
            json={}
        )
        
        assert approve_response.status_code == 200
        assert approve_response.json()["nim"] is not None
        
        # Check NIM format: YYYY001-0001
        nim = approve_response.json()["nim"]
        import re
        assert re.match(r'^\d{4}001-\d{4}$', nim)
    
    def test_approve_idempotent_no_duplicate_nim(self, setup_master_data):
        """Test approve yang idempotent (tidak generate NIM baru jika sudah ada)"""
        # Register
        reg_response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        calon_id = reg_response.json()["id"]
        
        # Approve first time
        approve1 = client.put(
            f"/api/pmb/approve/{calon_id}",
            json={}
        )
        nim1 = approve1.json()["nim"]
        
        # Approve second time (idempotent)
        approve2 = client.put(
            f"/api/pmb/approve/{calon_id}",
            json={}
        )
        nim2 = approve2.json()["nim"]
        
        # Should return same NIM
        assert nim1 == nim2
    
    def test_approve_nim_sequential(self, setup_master_data):
        """Test NIM generator menghasilkan sequential number"""
        # Register 3 calon dengan prodi yang sama
        nims = []
        for i in range(3):
            reg_response = client.post(
                "/api/pmb/register",
                json={
                    "nama_lengkap": f"Calon {i}",
                    "email": f"calon{i}@email.com",
                    "phone": f"0821234567{i:02d}",
                    "tanggal_lahir": "2005-01-15",
                    "alamat": "Jl. Test",
                    "program_studi_id": 1,  # Kode: 001
                    "jalur_masuk_id": 1
                }
            )
            calon_id = reg_response.json()["id"]
            
            approve_response = client.put(
                f"/api/pmb/approve/{calon_id}",
                json={}
            )
            nims.append(approve_response.json()["nim"])
        
        # Check sequential: ...0001, ...0002, ...0003
        assert nims[0][-4:] == "0001"
        assert nims[1][-4:] == "0002"
        assert nims[2][-4:] == "0003"
    
    def test_approve_not_found(self, setup_master_data):
        """Test approve calon yang tidak ada"""
        response = client.put(
            "/api/pmb/approve/999",
            json={}
        )
        assert response.status_code == 404
        assert "tidak ditemukan" in response.json()["detail"]


# ================== STATUS CHECK TESTS ==================

class TestPMBStatus:
    """Test PMB status check"""
    
    def test_get_registration_status_success(self, setup_master_data):
        """Test get status calon mahasiswa yang terdaftar"""
        # Register
        reg_response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        calon_id = reg_response.json()["id"]
        
        # Check status
        status_response = client.get(f"/api/pmb/status/{calon_id}")
        assert status_response.status_code == 200
        assert status_response.json()["id"] == calon_id
        assert status_response.json()["status"] == "pending"
    
    def test_get_registration_status_not_found(self, setup_master_data):
        """Test get status calon yang tidak ada"""
        response = client.get("/api/pmb/status/999")
        assert response.status_code == 404


# ================== STATISTICS TESTS ==================

class TestPMBStatistics:
    """Test PMB statistics endpoint"""
    
    def test_get_stats_empty(self, setup_master_data):
        """Test get stats tanpa data"""
        response = client.get("/api/pmb/stats")
        assert response.status_code == 200
        assert response.json()["total_pendaftar"] == 0
        assert response.json()["pending"] == 0
        assert response.json()["approved"] == 0
    
    def test_get_stats_with_data(self, setup_master_data):
        """Test get stats dengan data"""
        # Register 2 calon
        for i in range(2):
            client.post(
                "/api/pmb/register",
                json={
                    "nama_lengkap": f"Calon {i}",
                    "email": f"calon{i}@email.com",
                    "phone": f"0821234567{i:02d}",
                    "tanggal_lahir": "2005-01-15",
                    "alamat": "Jl. Test",
                    "program_studi_id": 1,
                    "jalur_masuk_id": 1
                }
            )
        
        response = client.get("/api/pmb/stats")
        assert response.status_code == 200
        assert response.json()["total_pendaftar"] == 2
        assert response.json()["pending"] == 2
        assert response.json()["approved"] == 0
        assert "Teknik Informatika" in response.json()["program_studi_counts"]


# ================== INTEGRATION TESTS ==================

class TestIntegration:
    """Integration tests - full workflow"""
    
    def test_full_workflow(self, setup_master_data):
        """Test full workflow: register -> check status -> approve -> generate NIM"""
        # 1. Register
        reg_response = client.post(
            "/api/pmb/register",
            json={
                "nama_lengkap": "Ahmad Hidayat",
                "email": "ahmad@email.com",
                "phone": "082123456789",
                "tanggal_lahir": "2005-01-15",
                "alamat": "Jl. Merdeka No. 10, Jakarta",
                "program_studi_id": 1,
                "jalur_masuk_id": 1
            }
        )
        assert reg_response.status_code == 201
        calon_id = reg_response.json()["id"]
        assert reg_response.json()["status"] == "pending"
        
        # 2. Check status (should be pending)
        status_response = client.get(f"/api/pmb/status/{calon_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "pending"
        assert status_response.json()["nim"] is None
        
        # 3. Approve and generate NIM
        approve_response = client.put(
            f"/api/pmb/approve/{calon_id}",
            json={}
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"
        nim = approve_response.json()["nim"]
        assert nim is not None
        
        # 4. Check status again (should be approved with NIM)
        final_status = client.get(f"/api/pmb/status/{calon_id}")
        assert final_status.status_code == 200
        assert final_status.json()["status"] == "approved"
        assert final_status.json()["nim"] == nim
