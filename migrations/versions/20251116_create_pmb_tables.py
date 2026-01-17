"""create pmb tables

Revision ID: 20251116_create_pmb_tables
Revises: 
Create Date: 2025-11-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251116_create_pmb_tables'
down_revision = None
branch_labels = None
depends_on = None

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
PHONE_REGEX = r"^(?:\+62|62|0)8[1-9][0-9]{6,10}$"


def upgrade():
    # Create program_studi table
    op.create_table(
        'program_studi',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kode', sa.String(length=3), nullable=False),
        sa.Column('nama', sa.String(length=255), nullable=False),
        sa.Column('fakultas', sa.String(length=255), nullable=False),
        sa.UniqueConstraint('kode', name='uq_program_studi_kode'),
    )

    # Create calon_mahasiswa table with a couple of constraints
    # For non-postgres DBs, skip DB-level regex constraints (they're Postgres `~` specific)
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    op.create_table(
        'calon_mahasiswa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nama_lengkap', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('tanggal_lahir', sa.Date(), nullable=False),
        sa.Column('alamat', sa.String(length=1024), nullable=True),
        sa.Column('program_studi_id', sa.Integer(), sa.ForeignKey('program_studi.id'), nullable=False),
        sa.Column('jalur_masuk', sa.Enum('SNBP', 'SNBT', 'Mandiri', name='jalur_masuk_enum'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='status_enum'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('email', name='uq_calon_mahasiswa_email'),
    )

    if is_postgres:
        # Add Postgres-only check constraints for email and phone regex
        op.create_check_constraint('ck_calon_mahasiswa_email_format', 'calon_mahasiswa', f"email ~ '{EMAIL_REGEX}'")
        op.create_check_constraint('ck_calon_mahasiswa_phone_indonesia', 'calon_mahasiswa', f"phone ~ '{PHONE_REGEX}'")


def downgrade():
    op.drop_table('calon_mahasiswa')
    op.drop_table('program_studi')
    # Drop enums — these are created in postgres when sa.Enum created
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS jalur_masuk_enum')
        op.execute('DROP TYPE IF EXISTS status_enum')
    # If Postgres created check constraints, those are dropped with the table
