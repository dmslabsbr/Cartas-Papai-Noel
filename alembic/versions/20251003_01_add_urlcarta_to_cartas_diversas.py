"""add urlcarta to cartas_diversas

Revision ID: 20251003_01
Revises: f2575f14a74c
Create Date: 2025-10-03
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251003_01'
down_revision = 'f2575f14a74c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tornar idempotente para evitar erro de coluna duplicada
    op.execute("ALTER TABLE public.cartas_diversas ADD COLUMN IF NOT EXISTS urlcarta TEXT")


def downgrade() -> None:
    # Tornar idempotente na remoção
    op.execute("ALTER TABLE public.cartas_diversas DROP COLUMN IF EXISTS urlcarta")
