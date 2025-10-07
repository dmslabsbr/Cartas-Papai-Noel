"""add idade and urlcarta_pq to cartas_diversas

Revision ID: add_idade_urlcarta_pq
Revises: f2575f14a74c
Create Date: 2025-10-06 22:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_idade_urlcarta_pq'
down_revision = '20251003_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('cartas_diversas', sa.Column('idade', sa.Integer(), nullable=True), schema='public')
    op.add_column('cartas_diversas', sa.Column('urlcarta_pq', sa.Text(), nullable=True), schema='public')


def downgrade() -> None:
    op.drop_column('cartas_diversas', 'urlcarta_pq', schema='public')
    op.drop_column('cartas_diversas', 'idade', schema='public')


