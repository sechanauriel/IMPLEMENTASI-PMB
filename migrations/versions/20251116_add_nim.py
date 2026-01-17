"""add nim column to calon_mahasiswa

Revision ID: 20251116_add_nim
Revises: 20251116_create_pmb_tables
Create Date: 2025-11-16 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251116_add_nim'
down_revision = '20251116_create_pmb_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('calon_mahasiswa', sa.Column('nim', sa.String(length=32), nullable=True))
    op.create_index('ix_calon_mahasiswa_nim', 'calon_mahasiswa', ['nim'])
    op.create_unique_constraint('uq_calon_mahasiswa_nim', 'calon_mahasiswa', ['nim'])


def downgrade():
    op.drop_constraint('uq_calon_mahasiswa_nim', 'calon_mahasiswa', type_='unique')
    op.drop_index('ix_calon_mahasiswa_nim', table_name='calon_mahasiswa')
    op.drop_column('calon_mahasiswa', 'nim')
