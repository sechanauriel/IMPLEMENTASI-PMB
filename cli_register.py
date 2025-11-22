#!/usr/bin/env python3
r"""CLI untuk mendaftar, approve calon mahasiswa ke database lokal (pmb.db).

Gunakan opsi CLI atau isi interaktif ketika menjalankan.

Contoh register (valid phone):
  .\.venv\Scripts\python.exe cli_register.py register --name Bima --email Bima@gmail.com --phone 081234567890 --dob 2000-01-01 --program 1 --jalur SNBP

Contoh approve (NIM sequential):
  .\.venv\Scripts\python.exe cli_register.py approve --id 1

Jika data duplikat (email) atau format tidak valid, program akan menampilkan pesan error dan keluar dengan kode != 0.
"""
from __future__ import annotations
import re
import sys
import argparse
from datetime import datetime, timezone
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Reuse models from project
from models import Base, ProgramStudi, CalonMahasiswa

# DB config (same file used by the app)
DATABASE_URL = "sqlite:///./pmb.db"

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
# Relaxed phone: minimal validation (at least 7 digits, possibly starting with +/0/6)
PHONE_REGEX = r"^[+0-9]{7,}$"


def validate_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email) is not None


def validate_phone(phone: str) -> bool:
    return re.match(PHONE_REGEX, phone) is not None


def get_session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


# Program studi yang tersedia
PROGRAM_STUDI_MAP = {
    "TIF": {"nama": "Teknik Informatika", "fakultas": "FTI"},
    "SI": {"nama": "Sistem Informasi", "fakultas": "FTI"},
    "FARM": {"nama": "Farmasi", "fakultas": "FIKES"},
    "MESIN": {"nama": "Teknik Mesin", "fakultas": "FT"},
}


def ensure_program_studi():
    """Ensure all program studi entries exist in database."""
    session = get_session()
    for kode, info in PROGRAM_STUDI_MAP.items():
        exists = session.query(ProgramStudi).filter(ProgramStudi.kode == kode).first()
        if not exists:
            ps = ProgramStudi(kode=kode, nama=info["nama"], fakultas=info["fakultas"])
            session.add(ps)
    session.commit()
    session.close()


def get_program_studi_id(kode: str) -> int | None:
    """Get program_studi_id by kode (e.g. 'TIF' -> 1)."""
    session = get_session()
    ps = session.query(ProgramStudi).filter(ProgramStudi.kode == kode).first()
    session.close()
    return ps.id if ps else None


def register(args) -> int:
    """Register a new candidate without NIM (status: pending)."""
    session = get_session()

    email = args.email.strip()
    phone = args.phone.strip()
    program_kode = args.program.upper()  # Convert to uppercase (e.g. 'tif' -> 'TIF')

    # Validate email
    if not validate_email(email):
        print(f"ERROR: Email tidak valid: {email}")
        return 2

    # Validate phone (relaxed: at least 7 digits)
    if not validate_phone(phone):
        print(f"ERROR: Nomor telepon tidak valid (minimal 7 digit): {phone}")
        return 3

    # Check program studi exists by kode
    prog = session.query(ProgramStudi).filter(ProgramStudi.kode == program_kode).first()
    if not prog:
        available = ", ".join(PROGRAM_STUDI_MAP.keys())
        print(f"ERROR: Program studi '{program_kode}' tidak ditemukan. Program tersedia: {available}")
        return 4

    # Check duplicate email
    exists = session.query(CalonMahasiswa).filter(func.lower(CalonMahasiswa.email) == email.lower()).first()
    if exists:
        print(f"ERROR: Email sudah terdaftar (DUPLIKAT): {email}")
        return 5

    # Parse tanggal_lahir
    try:
        tanggal = datetime.fromisoformat(args.dob).date()
    except Exception:
        print(f"ERROR: Format tanggal_lahir tidak valid (pakai YYYY-MM-DD): {args.dob}")
        return 7

    calon = CalonMahasiswa(
        nama_lengkap=args.name,
        email=email,
        phone=phone,
        tanggal_lahir=tanggal,
        alamat=args.alamat or None,
        program_studi_id=prog.id,
        jalur_masuk=args.jalur,
        status="pending",
    )

    session.add(calon)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"ERROR: Duplikat atau constraint violation: {e}")
        return 9
    except Exception as e:
        session.rollback()
        print(f"ERROR: Gagal menyimpan ke database: {e}")
        return 8

    session.refresh(calon)
    print("SUCCESS: Calon mahasiswa tersimpan dengan status PENDING:")
    print(f"  ID: {calon.id}")
    print(f"  Nama: {calon.nama_lengkap}")
    print(f"  Email: {calon.email}")
    print(f"  Phone: {calon.phone}")
    print(f"  Program Studi: {calon.program_studi.nama} ({calon.program_studi.kode})")
    print(f"  Status: {calon.status}")
    print(f"  NIM: {calon.nim}")
    return 0


def approve(args) -> int:
    """Approve a candidate and generate sequential NIM."""
    session = get_session()

    calon_id = args.id
    if calon_id is None:
        print("ERROR: --id diperlukan untuk approve")
        return 10

    calon = session.query(CalonMahasiswa).filter(CalonMahasiswa.id == calon_id).first()
    if not calon:
        print(f"ERROR: Calon mahasiswa dengan id {calon_id} tidak ditemukan (INVALID DATA)")
        return 11

    if calon.status == "approved":
        # Already approved, return existing NIM
        print(f"INFO: Calon sudah di-approve sebelumnya, NIM: {calon.nim}")
        return 0

    if calon.status != "pending":
        print(f"ERROR: Status calon tidak pending (current: {calon.status})")
        return 12

    # Generate sequential NIM: [tahun][kode_prodi][seq]
    year = datetime.now(timezone.utc).year
    kode = calon.program_studi.kode.upper()
    prefix = f"{year}{kode}"

    # Count existing NIMs with this prefix
    existing_count = session.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim.like(f"{prefix}%")
    ).count()

    for attempt in range(5):
        seq = existing_count + 1 + attempt
        nim_candidate = f"{prefix}{seq:04d}"
        calon.nim = nim_candidate
        calon.status = "approved"
        calon.approved_at = datetime.now(timezone.utc)

        try:
            session.add(calon)
            session.commit()
            session.refresh(calon)
            print(f"SUCCESS: Calon di-approve, NIM generated: {calon.nim}")
            return 0
        except IntegrityError:
            session.rollback()
            # Retry with next sequence
            continue

    print("ERROR: Gagal generate unique NIM setelah 5 percobaan")
    return 13


def main():
    # Ensure all program studi exist in DB first
    ensure_program_studi()
    
    parser = argparse.ArgumentParser(description="CLI register/approve calon mahasiswa ke pmb.db")
    subparsers = parser.add_subparsers(dest="command", help="Perintah")

    # Register subcommand
    register_parser = subparsers.add_parser("register", help="Daftar calon mahasiswa baru")
    register_parser.add_argument("--name", required=False, help="Nama lengkap")
    register_parser.add_argument("--email", required=False, help="Email")
    register_parser.add_argument("--phone", required=False, help="Nomor telepon")
    register_parser.add_argument("--dob", required=False, default="2000-01-01", help="Tanggal lahir YYYY-MM-DD")
    register_parser.add_argument("--alamat", required=False, default="", help="Alamat")
    register_parser.add_argument("--program", required=False, default="TIF", help=f"Kode program studi ({', '.join(PROGRAM_STUDI_MAP.keys())})")
    register_parser.add_argument("--jalur", required=False, default="SNBP", choices=["SNBP", "SNBT", "Mandiri"], help="Jalur masuk")

    # Approve subcommand
    approve_parser = subparsers.add_parser("approve", help="Approve dan generate NIM")
    approve_parser.add_argument("--id", type=int, required=False, help="ID calon mahasiswa")

    args = parser.parse_args()

    if args.command == "register":
        # If any required value missing, ask interactively
        if not args.name:
            args.name = input("Nama lengkap: ").strip()
        if not args.email:
            args.email = input("Email: ").strip()
        if not args.phone:
            args.phone = input("Nomor telepon: ").strip()
        if not args.alamat:
            args.alamat = input("Alamat (opsional): ").strip()

        rc = register(args)
        sys.exit(rc)

    elif args.command == "approve":
        if args.id is None:
            args.id = int(input("ID calon mahasiswa: ").strip())
        rc = approve(args)
        sys.exit(rc)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
