#!/usr/bin/env python
"""Simple server runner for PMB API with seed data"""
import uvicorn
from database import SessionLocal
from models import Base, ProgramStudi
from database import engine
from main import app

# Create DB metadata
Base.metadata.create_all(bind=engine)

# Seed initial program studi data
def seed_data():
    db = SessionLocal()
    try:
        if db.query(ProgramStudi).count() == 0:
            programs = [
                ProgramStudi(kode="TIF", nama="Teknik Informatika", fakultas="Teknik"),
                ProgramStudi(kode="SIB", nama="Sistem Informasi Bisnis", fakultas="Bisnis"),
                ProgramStudi(kode="KOM", nama="Komunikasi", fakultas="Ilmu Sosial"),
            ]
            db.add_all(programs)
            db.commit()
            print("[OK] Seed data loaded successfully")
        else:
            print("[OK] Seed data already exists")
    finally:
        db.close()

seed_data()

if __name__ == "__main__":
    print("Starting PMB API Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


