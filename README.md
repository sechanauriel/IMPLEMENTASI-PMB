# Sistem PMB (Penerimaan Mahasiswa Baru) 🎓

Sistem manajemen penerimaan mahasiswa baru dengan NIM auto-generate, form validation, dan REST API menggunakan FastAPI.

## 📋 Fitur Utama

- ✅ **Registrasi Calon Mahasiswa**: Form validasi lengkap dengan email & nomor telepon
- ✅ **NIM Auto-Generate**: Format `YYYY[KODE_PRODI][SEQUENTIAL]` (contoh: 2025001-0001)
- ✅ **Manajemen Status**: Pending → Approved → Generate NIM
- ✅ **Validasi Input**: Email unique, nomor telepon format Indonesia
- ✅ **Statistik Dashboard**: Total pendaftar, breakdown by prodi dan jalur masuk
- ✅ **REST API Lengkap**: Swagger documentation included
- ✅ **Thread-Safe NIM Generator**: Mencegah race condition
- ✅ **80%+ Test Coverage**: Unit tests dan integration tests

## 🛠️ Tech Stack

| Komponen | Technology |
|----------|-----------|
| Backend | FastAPI 0.104+ |
| Database | SQLite / MySQL |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic 2.0 |
| Migration | Alembic |
| Testing | pytest 7.4+ |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Create database tables
python -c "from app.database import init_db; init_db()"

# Insert master data (program studi dan jalur masuk)
python scripts/seed_data.py
```

### 3. Run Server

```bash
python main.py
```

Server akan berjalan di `http://localhost:8000`

### 4. Akses Dokumentasi

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Master Data

#### Create Program Studi
```http
POST /api/master/program-studi
Content-Type: application/json

{
  "kode": "001",
  "nama": "Teknik Informatika",
  "fakultas": "Teknik"
}
```

#### Get All Program Studi
```http
GET /api/master/program-studi
```

#### Create Jalur Masuk
```http
POST /api/master/jalur-masuk
Content-Type: application/json

{
  "kode": "SNBP",
  "nama": "Seleksi Nasional Berbasis Prestasi",
  "deskripsi": "Jalur SNBP untuk calon mahasiswa berprestasi"
}
```

#### Get All Jalur Masuk
```http
GET /api/master/jalur-masuk
```

### PMB Registration

#### Register Calon Mahasiswa
```http
POST /api/pmb/register
Content-Type: application/json

{
  "nama_lengkap": "Ahmad Hidayat",
  "email": "ahmad.hidayat@email.com",
  "phone": "082123456789",
  "tanggal_lahir": "2005-01-15",
  "alamat": "Jl. Merdeka No. 10, Jakarta",
  "program_studi_id": 1,
  "jalur_masuk_id": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "nama_lengkap": "Ahmad Hidayat",
  "email": "ahmad.hidayat@email.com",
  "phone": "+628123456789",
  "tanggal_lahir": "2005-01-15",
  "alamat": "Jl. Merdeka No. 10, Jakarta",
  "program_studi_id": 1,
  "jalur_masuk_id": 1,
  "status": "pending",
  "nim": null,
  "created_at": "2025-01-20T12:00:00",
  "approved_at": null,
  "updated_at": "2025-01-20T12:00:00",
  "program_studi": {
    "id": 1,
    "kode": "001",
    "nama": "Teknik Informatika",
    "fakultas": "Teknik",
    "created_at": "2025-01-20T11:00:00",
    "updated_at": "2025-01-20T11:00:00"
  },
  "jalur_masuk": {
    "id": 1,
    "kode": "SNBP",
    "nama": "Seleksi Nasional Berbasis Prestasi",
    "created_at": "2025-01-20T11:00:00"
  }
}
```

#### Get Registration Status
```http
GET /api/pmb/status/{calon_id}
```

#### Approve & Generate NIM
```http
PUT /api/pmb/approve/{calon_id}
Content-Type: application/json

{}
```

**Response:**
```json
{
  "id": 1,
  "nim": "2025001-0001",
  "nama_lengkap": "Ahmad Hidayat",
  "email": "ahmad.hidayat@email.com",
  "program_studi": "Teknik Informatika",
  "status": "approved"
}
```

#### Get List Calon Mahasiswa
```http
GET /api/pmb/list?status=pending&skip=0&limit=10
```

#### Get Statistics
```http
GET /api/pmb/stats
```

**Response:**
```json
{
  "total_pendaftar": 150,
  "pending": 80,
  "approved": 60,
  "rejected": 10,
  "program_studi_counts": {
    "Teknik Informatika": 45,
    "Sistem Informasi": 35,
    "Teknik Komputer": 30
  },
  "jalur_masuk_counts": {
    "SNBP": 50,
    "SNBT": 80,
    "Mandiri": 20
  }
}
```

#### Reject Calon
```http
POST /api/pmb/reject/{calon_id}
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage Report
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Class
```bash
pytest tests/test_pmb.py::TestPMBRegistration -v
```

### Run Specific Test
```bash
pytest tests/test_pmb.py::TestPMBRegistration::test_register_success -v
```

## 📊 Test Coverage

Sistem ini memiliki comprehensive test coverage:

### 1. **Master Data Tests** ✅
- Create Program Studi (success & duplicate)
- List Program Studi
- Create Jalur Masuk (success & duplicate)
- List Jalur Masuk

### 2. **Registration Tests** ✅
- Register success
- Duplicate email validation
- Invalid email format
- Invalid phone format
- Valid phone formats (Indonesian)
- Invalid program studi
- Invalid jalur masuk
- Short nama validation

### 3. **Approval & NIM Generation Tests** ✅
- Approve dan generate NIM
- Idempotent approval (tidak generate NIM baru)
- Sequential NIM generation
- Approve non-existent calon

### 4. **Utility Tests** ✅
- NIM format validation
- NIM parsing
- Phone normalization (0→+62)
- Email validation
- Thread-safety

### 5. **Integration Tests** ✅
- Full workflow: Register → Status → Approve → NIM

## 📁 Project Structure

```
pmb_sistem/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── calon_mahasiswa.py  # Main model
│   │   ├── program_studi.py
│   │   └── jalur_masuk.py
│   ├── schemas/
│   │   └── __init__.py         # Pydantic models
│   ├── routers/
│   │   ├── pmb.py              # PMB endpoints
│   │   └── master_data.py      # Master data endpoints
│   └── utils/
│       ├── nim_generator.py    # NIM generation logic
│       └── validators.py       # Validation utilities
├── tests/
│   ├── test_pmb.py             # API tests
│   └── test_utils.py           # Utility tests
├── requirements.txt
├── README.md
└── main.py                      # Entry point
```

## 🔐 Validasi & Constraints

### Email
- Format: `user@domain.com`
- Harus unique dalam database
- Case-insensitive

### Nomor Telepon Indonesia
- Format: `0812345678XX` atau `+628123456789`
- Minimal 10 digit setelah kode negara
- Maksimal 15 digit total
- Auto-normalize ke format `+62XXXXXXXXX`

### Nama Lengkap
- Minimal 3 karakter
- Auto-trim whitespace

### Alamat
- Minimal 5 karakter
- Auto-trim whitespace

### NIM Generator
- Format: `YYYY[KODE_PRODI][RUNNING_NUMBER]`
- Contoh: `2025001-0001`
- **Thread-safe**: Mencegah duplicate NIM via locking
- **Idempotent**: Tidak generate ulang jika sudah ada
- **Sequential**: Running number auto-increment per prodi per tahun

## 🐛 Error Handling

| Status Code | Scenario |
|------------|----------|
| 201 | Registrasi berhasil |
| 200 | Operasi berhasil |
| 400 | Input validation error (invalid format, invalid prodi, dll) |
| 404 | Resource tidak ditemukan |
| 409 | Conflict (email sudah terdaftar) |
| 422 | Pydantic validation error |

## 📝 Contoh Use Case

### Workflow Lengkap

```python
# 1. Create master data
POST /api/master/program-studi
{
  "kode": "001",
  "nama": "Teknik Informatika",
  "fakultas": "Teknik"
}

POST /api/master/jalur-masuk
{
  "kode": "SNBP",
  "nama": "SNBP 2025"
}

# 2. Calon registers
POST /api/pmb/register
{
  "nama_lengkap": "Ahmad Hidayat",
  "email": "ahmad@email.com",
  "phone": "082123456789",
  ...
}
→ Returns: { "id": 1, "status": "pending", "nim": null }

# 3. Check status
GET /api/pmb/status/1
→ Returns: { "id": 1, "status": "pending", "nim": null }

# 4. Admin approves
PUT /api/pmb/approve/1
→ Returns: { "id": 1, "nim": "2025001-0001", "status": "approved" }

# 5. Verify final status
GET /api/pmb/status/1
→ Returns: { "id": 1, "status": "approved", "nim": "2025001-0001" }

# 6. Get statistics
GET /api/pmb/stats
→ Returns: { "total_pendaftar": 1, "approved": 1, ... }
```

## 🎓 Learning Outcomes

Dari implementasi sistem ini, Anda akan belajar:

1. **OOP & Design Patterns**
   - Class inheritance (ProgramStudi, JalurMasuk)
   - Enum untuk status
   - Relationship (calon ↔ prodi)

2. **Database Design**
   - SQLAlchemy ORM
   - Foreign key constraints
   - Unique constraints
   - Indexes untuk performance

3. **API Design**
   - RESTful principles
   - Error handling
   - Dependency injection
   - Response formatting

4. **Validation & Security**
   - Input validation (Pydantic)
   - Email & phone format
   - Duplicate prevention
   - Thread-safe operations

5. **Testing**
   - Unit tests
   - Integration tests
   - Fixtures
   - Mocking

6. **Concurrency**
   - Threading locks
   - Race condition prevention
   - Idempotency

## 📞 Troubleshooting

### Database Already Locked Error
```bash
# Delete old database dan buat baru
rm pmb.db
python main.py
```

### Import Errors
```bash
# Pastikan PYTHONPATH benar
export PYTHONPATH="${PYTHONPATH}:/path/to/pmb_sistem"
python main.py
```

### Port Already in Use
```bash
# Change port in main.py
uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
```

## 📄 License

MIT License - untuk tujuan pembelajaran

## 🤝 Contributing

Silakan buat improvements:
1. Add validation untuk field lain
2. Implement soft delete untuk calon
3. Add pagination lebih advanced
4. Implement caching untuk stats
5. Add file upload untuk dokumen

---

**Dibuat untuk pembelajaran OOP dan Backend Development** 🚀
