"""
Seed database dengan master data awal
"""

from app.database import SessionLocal, init_db
from app.models import ProgramStudi, JalurMasuk

def seed_data():
    """Insert master data"""
    
    db = SessionLocal()
    
    # Initialize database
    init_db()
    
    # Check if data already exists
    if db.query(ProgramStudi).first():
        print("Data sudah ada, skip seeding")
        db.close()
        return
    
    # Create Program Studi
    program_studi_list = [
        ProgramStudi(kode="001", nama="Teknik Informatika", fakultas="Teknik"),
        ProgramStudi(kode="002", nama="Sistem Informasi", fakultas="Teknik"),
        ProgramStudi(kode="003", nama="Teknik Komputer", fakultas="Teknik"),
        ProgramStudi(kode="101", nama="Manajemen", fakultas="Ekonomi & Bisnis"),
        ProgramStudi(kode="102", nama="Akuntansi", fakultas="Ekonomi & Bisnis"),
        ProgramStudi(kode="201", nama="Biologi", fakultas="MIPA"),
        ProgramStudi(kode="202", nama="Kimia", fakultas="MIPA"),
    ]
    
    db.add_all(program_studi_list)
    db.commit()
    
    # Create Jalur Masuk
    jalur_masuk_list = [
        JalurMasuk(
            kode="SNBP",
            nama="Seleksi Nasional Berbasis Prestasi",
            deskripsi="Seleksi berdasarkan prestasi akademik di sekolah"
        ),
        JalurMasuk(
            kode="SNBT",
            nama="Seleksi Nasional Berbasis Tes",
            deskripsi="Seleksi melalui tes kemampuan akademik"
        ),
        JalurMasuk(
            kode="MANDIRI",
            nama="Jalur Mandiri",
            deskripsi="Seleksi mandiri oleh kampus"
        ),
    ]
    
    db.add_all(jalur_masuk_list)
    db.commit()
    
    print("✅ Master data seeded successfully!")
    print(f"   - {len(program_studi_list)} Program Studi")
    print(f"   - {len(jalur_masuk_list)} Jalur Masuk")
    
    db.close()


if __name__ == "__main__":
    seed_data()
