"""add grupos table and new fields to cartas_diversas

Revision ID: 20251021_01
Revises: add_idade_urlcarta_pq
Create Date: 2025-10-21
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251021_01'
down_revision = 'add_idade_urlcarta_pq'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create table public.grupos
    op.create_table(
        'grupos',
        sa.Column('id_grupo', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('ds_grupo', sa.Text(), nullable=False),
        schema='public'
    )

    # Seed initial groups
    op.execute("INSERT INTO public.grupos (id_grupo, ds_grupo) VALUES (1, 'Correios') ON CONFLICT DO NOTHING;")
    op.execute("INSERT INTO public.grupos (id_grupo, ds_grupo) VALUES (2, 'Terceirizados') ON CONFLICT DO NOTHING;")

    # Add columns to public.cartas_diversas
    op.add_column('cartas_diversas', sa.Column('id_grupo_key', sa.Integer(), nullable=True), schema='public')
    op.add_column('cartas_diversas', sa.Column('cod_carta', sa.Integer(), nullable=True), schema='public')

    # Optional: FK to grupos
    op.create_foreign_key(
        'fk_cartas_diversas_grupo',
        'cartas_diversas',
        'grupos',
        ['id_grupo_key'],
        ['id_grupo'],
        source_schema='public',
        referent_schema='public',
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop FK
    op.drop_constraint('fk_cartas_diversas_grupo', 'cartas_diversas', type_='foreignkey', schema='public')

    # Drop columns
    op.drop_column('cartas_diversas', 'cod_carta', schema='public')
    op.drop_column('cartas_diversas', 'id_grupo_key', schema='public')

    # Drop table grupos
    op.drop_table('grupos', schema='public')


