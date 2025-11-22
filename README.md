# PMB Database schema, API, and Tests

This repository contains a complete PMB (Penerimaan Mahasiswa Baru / New Student Admissions) system with:
- SQLAlchemy ORM models and Alembic migrations
- FastAPI REST API with 3 endpoints
- Thread-safe NIM (Student ID) generator with database-level locking
- Comprehensive pytest test suite with 5 passing tests

## Schema
- `program_studi` — id, kode (3 chars, unique), nama, fakultas
- `calon_mahasiswa` — id, nama_lengkap, email (unique), phone (Indonesia format validation), tanggal_lahir, alamat, program_studi_id (FK), jalur_masuk (SNBP/SNBT/Mandiri), status (pending/approved/rejected), created_at, approved_at, nim (unique, nullable)
- `nim_counters` — id, year, kode_prodi (per-program counter for sequential NIM generation), last_seq, unique constraint on (year, kode_prodi)

Both phone and email have DB-level check constraints using regular expressions (Postgres-style `~` operator). Additionally, Python-level validation in `models.py` raises ValueError when invalid data is assigned.

## Files
- `models.py` — SQLAlchemy ORM models: `ProgramStudi`, `CalonMahasiswa`, `NIMCounter`
- `schemas.py` — Pydantic v1-style validation schemas for request/response
- `database.py` — SQLAlchemy engine, session factory, and FastAPI dependency
- `main.py` — FastAPI app with 3 endpoints: POST /register, PUT /approve/{id}, GET /status/{id}
- `utils.py` — Thread-safe NIM generator with row-level DB locking
- `migrations/versions/` — 3 Alembic migration scripts
- `tests/test_pmb.py` — Pytest suite with 5 passing tests
- `requirements.txt` — Dependencies

## Installing dependencies

In a virtual environment, run:

```powershell
pip install -r requirements.txt
```

## Running the FastAPI server (development)

```powershell
# Optional: set DATABASE_URL; defaults to sqlite:///./pmb.db
# export DATABASE_URL="sqlite:///./pmb.db"
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### API Endpoints

**POST /register** — Register a new candidate
- Request body: `{nama_lengkap, email, phone, tanggal_lahir, alamat, program_studi_id, jalur_masuk}`
- Response: 201 with candidate object (status='pending')
- Error: 400 (invalid program_studi_id), 409 (duplicate email), 422 (validation error)

**PUT /approve/{id}** — Approve a candidate and generate NIM
- Response: 200 with `{nim: "YYYYKODXXXX"}` (e.g., "2025TIF0001")
- Error: 404 (not found), 409 (not pending status or NIM conflict)

**GET /status/{id}** — Get candidate status
- Response: 200 with full candidate object
- Error: 404 (not found)

## Running tests

```powershell
pytest tests/test_pmb.py -v
```

All 5 tests pass:
- `test_register_success` — Verify POST /register returns 201 with correct data
- `test_register_duplicate_email` — Verify duplicate email returns 409
- `test_approve_generate_nim` — Verify sequential NIM generation (0001, 0002...)
- `test_approve_idempotent` — Verify approving same candidate twice returns same NIM
- `test_invalid_phone_format` — Verify invalid phone returns 422 validation error

## Implementation Details

### Thread-Safe NIM Generation
The `generate_nim()` function uses SQLAlchemy's `.with_for_update()` method to obtain row-level database locks on the `NIMCounter` table, ensuring atomic sequential NIM generation even under concurrent requests.

### Pydantic Validation
Uses Pydantic v1-style validators (`@validator`) to validate email (using EmailStr), phone format (Indonesia +62/62/0 followed by 8 digits), and jalur_masuk enum values.

## API endpoints
- POST /register — register calon mahasiswa. Returns the created record with `status: pending`.
- PUT /approve/{id} — approve calon with given id. Generates NIM in format [year][kode_prodi][sequential], stores it and returns `{"nim": "..."}`. Returns 404 if not found, 409 on conflict or if status prevents approval.
- GET /status/{id} — returns the calon mahasiswa data + status.

Use `DATABASE_URL` environment variable to point to your DB. For example (Postgres):

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:pass@localhost:5432/dbname"
```

## Alembic setup and running migrations

If you already have Alembic initialized in your project, put the provided migration file into `migrations/versions/` and run:

```powershell
# set correct DB URL in alembic.ini or export env var ALEMBIC_URL
alembic upgrade head
```

Note: The CheckConstraints that use `~` operators are Postgres-specific. If you use MySQL or SQLite, you may need to adapt the constraints or rely on Python-level validation.

## Notes on validation
- Email: basic regex allows common valid emails but is not RFC 5322 exhaustive.
- Phone: enforces Indonesia formats starting with +62/62/0 and then '8...' — common for mobile numbers.

---

If you prefer DB-agnostic constraints, I can add more portable checks (e.g., prefix checks and length) and/or generate a Postgres-specific migration. Tell me which database you plan to use. 
