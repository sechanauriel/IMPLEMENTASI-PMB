"""initial pmb schema

Revision ID: 20251117_initial_schema
Revises: 
Create Date: 2025-11-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251117_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
PHONE_SIMPLE_CHECK = "(phone LIKE '+62%' OR phone LIKE '62%' OR phone LIKE '0%')"


def upgrade():
    # Create program_studi
    op.create_table(
        'program_studi',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kode', sa.String(length=3), nullable=False),
        sa.Column('nama', sa.String(length=255), nullable=False),
        sa.Column('fakultas', sa.String(length=255), nullable=False),
        sa.UniqueConstraint('kode', name='uq_program_studi_kode'),
    )

    # Create calon_mahasiswa with email unique, phone basic check, status and jalur enums
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
        sa.Column('nim', sa.String(length=32), nullable=True),
        sa.UniqueConstraint('email', name='uq_calon_mahasiswa_email'),
        sa.UniqueConstraint('nim', name='uq_calon_mahasiswa_nim'),
    )

    # Create a basic CHECK constraint for phone format on non-postgres DBs
    if not is_postgres:
        # Simple check: must start with +62, 62 or 0
        op.create_check_constraint('ck_calon_mahasiswa_phone_basic', 'calon_mahasiswa', PHONE_SIMPLE_CHECK)
    else:
        # For Postgres, add regex checks for better validation
        op.create_check_constraint('ck_calon_mahasiswa_email_format', 'calon_mahasiswa', f"email ~ '{EMAIL_REGEX}'")
        op.create_check_constraint('ck_calon_mahasiswa_phone_indonesia', 'calon_mahasiswa', "phone ~ '^(?:\\+62|62|0)8[1-9][0-9]{6,10}$'")

    # Index on nim
    op.create_index('ix_calon_mahasiswa_nim', 'calon_mahasiswa', ['nim'])

    # Create nim_counters table to support sequential NIM generation
    op.create_table(
        'nim_counters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('kode_prodi', sa.String(length=10), nullable=False),
        sa.Column('last_seq', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('year', 'kode_prodi', name='uq_nimcounter_year_kode'),
    )


def downgrade():
    # Drop in reverse order
    op.drop_table('nim_counters')
    op.drop_index('ix_calon_mahasiswa_nim', table_name='calon_mahasiswa')
    op.drop_table('calon_mahasiswa')
    op.drop_table('program_studi')
    # Drop enum types for Postgres
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS jalur_masuk_enum')
        op.execute('DROP TYPE IF EXISTS status_enum')
