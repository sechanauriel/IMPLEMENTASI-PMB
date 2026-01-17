import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator, cast

# Create test engine BEFORE importing main/database to replace the module-level engine
# Use StaticPool to avoid per-connection SQLite databases in memory
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Mock database.engine before importing main
# Ensure project root is on sys.path so tests can be run directly with `python tests/test_pmb.py`
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import database
original_get_db = database.get_db  # Save original function
database.engine = test_engine
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

import main
from models import Base, ProgramStudi

# Create all tables in test engine
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    # Clear all tables before each test to ensure isolation
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Update SessionLocal to ensure fresh sessions
    database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create fresh session from test_engine for each test
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    # Override the get_db dependency to always return our test db_session
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass
    
    main.app.dependency_overrides[main.get_db] = override_get_db
    
    with TestClient(main.app) as c:
        yield c
    
    main.app.dependency_overrides.clear()


def create_program(db_session: Session, kode: str = "TIF") -> ProgramStudi:
    ps = ProgramStudi(kode=kode, nama="Teknik Informatika", fakultas="FTI")
    db_session.add(ps)
    db_session.commit()
    db_session.refresh(ps)
    return ps


def test_register_success(client: TestClient, db_session: Session) -> None:
    ps = create_program(db_session)

    # Tambahkan data program studi agar database siap digunakan
    # Sudah dilakukan oleh create_program di setiap test

    payload: dict[str, str | int] = {
        "nama_lengkap": "Budi",
        "email": "budi@example.com",
        "phone": "+628123456789",
        "tanggal_lahir": "2004-01-01",
        "alamat": "Jl. Contoh 1",
        "program_studi_id": cast(int, ps.id),
        "jalur_masuk": "SNBP",
    }

    r = client.post("/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["status"] == "pending"
    assert data["email"] == payload["email"]

    r = client.post("/register", json=payload)
    # Duplicate registration should return 409 Conflict
    assert r.status_code == 409


def test_register_duplicate_email(client: TestClient, db_session: Session) -> None:
    ps = create_program(db_session)

    payload = {
        "nama_lengkap": "Siti",
        "email": "siti@example.com",
        "phone": "+628111111111",
        "tanggal_lahir": "2004-05-06",
        "alamat": "Jl. Contoh 2",
        "program_studi_id": ps.id,
        "jalur_masuk": "SNBT",
    }

    r1 = client.post("/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/register", json=payload)
    assert r2.status_code == 409


def test_approve_generate_nim(client: TestClient, db_session: Session) -> None:
    # create a program with kode TST
    ps = create_program(db_session, kode="TST")

    payload1 = {
        "nama_lengkap": "Andi",
        "email": "andi1@example.com",
        "phone": "+628123450001",
        "tanggal_lahir": "2003-02-02",
        "alamat": "Jl. Test 1",
        "program_studi_id": ps.id,
        "jalur_masuk": "Mandiri",
    }
    payload2 = {
        "nama_lengkap": "Andi2",
        "email": "andi2@example.com",
        "phone": "+628123450002",
        "tanggal_lahir": "2003-03-03",
        "alamat": "Jl. Test 2",
        "program_studi_id": ps.id,
        "jalur_masuk": "Mandiri",
    }

    r1 = client.post("/register", json=payload1)
    assert r1.status_code == 201
    id1 = r1.json()["id"]

    r2 = client.post("/register", json=payload2)
    assert r2.status_code == 201
    id2 = r2.json()["id"]

    # Approve first
    a1 = client.put(f"/approve/{id1}")
    assert a1.status_code == 200
    nim1 = a1.json().get("nim")
    assert nim1 is not None

    from datetime import datetime
    import re
    year = datetime.now().year
    prefix = f"{year}{ps.kode}"
    assert re.match(rf"^{prefix}\d{{4}}$", nim1)
    assert nim1.endswith("0001")

    # Approve second -> expect sequential 0002
    a2 = client.put(f"/approve/{id2}")
    assert a2.status_code == 200
    nim2 = a2.json().get("nim")
    assert nim2 is not None
    assert nim2.endswith("0002")


def test_approve_idempotent(client: TestClient, db_session: Session) -> None:
    ps = create_program(db_session, kode="TST")

    payload = {
        "nama_lengkap": "Ida",
        "email": "ida@example.com",
        "phone": "+628123450010",
        "tanggal_lahir": "2002-07-07",
        "alamat": "Jl. Test 10",
        "program_studi_id": ps.id,
        "jalur_masuk": "SNBT",
    }

    r = client.post("/register", json=payload)
    assert r.status_code == 201
    cid = r.json()["id"]

    a1 = client.put(f"/approve/{cid}")
    assert a1.status_code == 200
    nim_first = a1.json().get("nim")

    # Approve again should return same NIM
    a2 = client.put(f"/approve/{cid}")
    assert a2.status_code == 200
    nim_second = a2.json().get("nim")
    assert nim_first == nim_second


def test_invalid_phone_format(client: TestClient, db_session: Session) -> None:
    ps = create_program(db_session)

    payload = {
        "nama_lengkap": "X",
        "email": "x@example.com",
        "phone": "+123",
        "tanggal_lahir": "2000-01-01",
        "alamat": "Nowhere",
        "program_studi_id": ps.id,
        "jalur_masuk": "SNBP",
    }

    r = client.post("/register", json=payload)
    assert r.status_code == 422


def test_register_email_dito_and_duplicate(client: TestClient, db_session: Session) -> None:
    ps = create_program(db_session)

    payload = {
        "nama_lengkap": "Dito",
        "email": "dito@gmail.com",
        "phone": "+628123456780",
        "tanggal_lahir": "2001-01-01",
        "alamat": "Jl. Dito 1",
        "program_studi_id": ps.id,
        "jalur_masuk": "SNBP",
    }

    r1 = client.post("/register", json=payload)
    assert r1.status_code == 201

    # Duplicate registration should error
    r2 = client.post("/register", json=payload)
    assert r2.status_code == 409


def test_nim_generator_sequence_12345(client: TestClient, db_session: Session) -> None:
    # Create program with kode TST
    ps = create_program(db_session, kode="TST")

    # Candidate to approve
    payload = {
        "nama_lengkap": "SeqTest",
        "email": "seqtest@example.com",
        "phone": "+628123450099",
        "tanggal_lahir": "2000-12-12",
        "alamat": "Jl. Seq",
        "program_studi_id": ps.id,
        "jalur_masuk": "Mandiri",
    }

    r = client.post("/register", json=payload)
    assert r.status_code == 201
    cid = r.json()["id"]

    # Pre-insert a large number of dummy NIMs so the next sequence becomes 12345
    # We'll insert 12344 dummy approved calon_mahasiswa rows with nim prefix + seq
    from datetime import datetime
    year = datetime.now().year
    prefix = f"{year}{ps.kode}"

    bulk = []
    for seq in range(1, 12345):
        # stop before 12345, so last existing seq = 12344
        nim_val = f"{prefix}{seq:04d}"
        bulk.append({
            "nama_lengkap": f"dummy{seq}",
            "email": f"dummy{seq}@example.com",
            "phone": "+628100000000",
            "tanggal_lahir": "1990-01-01",
            "alamat": "dummy",
            "program_studi_id": ps.id,
            "jalur_masuk": "SNBP",
            "status": "approved",
            "nim": nim_val,
        })

    # Bulk insert using raw SQL for performance
    from sqlalchemy import text
    insert_sql = text(
        "INSERT INTO calon_mahasiswa (nama_lengkap, email, phone, tanggal_lahir, alamat, program_studi_id, jalur_masuk, status, nim, created_at) "
        "VALUES (:nama_lengkap, :email, :phone, :tanggal_lahir, :alamat, :program_studi_id, :jalur_masuk, :status, :nim, CURRENT_TIMESTAMP)"
    )

    for row in bulk:
        db_session.execute(insert_sql, params=row)
    db_session.commit()

    # Now approve our candidate; expected sequence is 12345
    a = client.put(f"/approve/{cid}")
    assert a.status_code == 200
    nim = a.json().get("nim")
    assert nim is not None
    assert nim.endswith("12345")


def test_approve_invalid_id_returns_404(client: TestClient, db_session: Session) -> None:
    # Approving a non-existent id should return 404
    r = client.put("/approve/999999")
    assert r.status_code == 404
