"""create nim_counters table

Revision ID: 20251116_create_nim_counters
Revises: 20251116_add_nim
Create Date: 2025-11-16 00:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251116_create_nim_counters'
down_revision = '20251116_add_nim'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'nim_counters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('kode_prodi', sa.String(length=10), nullable=False),
        sa.Column('last_seq', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('year', 'kode_prodi', name='uq_nimcounter_year_kode'),
    )


def downgrade():
    op.drop_table('nim_counters')
