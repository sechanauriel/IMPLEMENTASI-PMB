from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import NIMCounter


def generate_nim(tahun: int, kode_prodi: str, db: Session) -> str:
    """
    Generate NIM format: YYYY[KODE]XXXX
    Example: 2025TIF0001

    Uses a per-(year,kode) counter row and obtains a row-level lock to
    increment the counter atomically. Returns the formatted NIM.
    
    Note: Assumes db session is already in a transaction; do not start a new one.
    """
    kode = kode_prodi.strip().upper()
    if not kode:
        raise ValueError("kode_prodi must be a non-empty string")
    if tahun < 2000 or tahun > 9999:
        raise ValueError("tahun must be a four-digit year")

    try:
        q = db.query(NIMCounter).filter(
            NIMCounter.year == tahun,
            NIMCounter.kode_prodi == kode,
        ).with_for_update()

        counter = q.one_or_none()

        if counter is None:
            counter = NIMCounter(year=tahun, kode_prodi=kode, last_seq=1)
            db.add(counter)
            db.flush()
            seq = 1
        else:
            # Ensure we operate on plain int to avoid SQLAlchemy instrumented attribute issues
            seq = int(counter.last_seq) + 1
            counter.last_seq = seq
            db.add(counter)
            db.flush()

        nim = f"{tahun}{kode}{seq:04d}"
        return nim
    except SQLAlchemyError:
        # Let caller handle DB errors (retry/translate to HTTP errors)
        raise