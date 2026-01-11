"""add anatel tables

Revision ID: 3b1d1f0c0a2f
Revises: 9c81d8d1c4aa
Create Date: 2026-01-11 01:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '3b1d1f0c0a2f'
down_revision = '9c81d8d1c4aa'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS anatel")

    op.create_table(
        'anatel_stations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('source_id', sa.Text(), nullable=True),
        sa.Column('service', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('uf', sa.Text(), nullable=True),
        sa.Column('municipio', sa.Text(), nullable=True),
        sa.Column('cod_municipio', sa.Text(), nullable=True),
        sa.Column('canal', sa.Text(), nullable=True),
        sa.Column('frequencia_mhz', sa.Float(), nullable=True),
        sa.Column('classe', sa.Text(), nullable=True),
        sa.Column('erp_kw', sa.Float(), nullable=True),
        sa.Column('altura_m', sa.Float(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('fistel', sa.Text(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('pattern_dbd', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('limitacoes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4674, from_text='ST_GeomFromEWKT', name='geometry', nullable=False, spatial_index=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='anatel',
    )
    op.create_index('idx_anatel_stations_geom', 'anatel_stations', ['geom'], unique=False, postgresql_using='gist', schema='anatel')
    op.create_index('idx_anatel_stations_service', 'anatel_stations', ['service'], unique=False, schema='anatel')

    op.create_table(
        'aerodromes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('icao', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('uf', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('kind', sa.Text(), nullable=True),
        sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4674, from_text='ST_GeomFromEWKT', name='geometry', nullable=False, spatial_index=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='anatel',
    )
    op.create_index('idx_aerodromes_geom', 'aerodromes', ['geom'], unique=False, postgresql_using='gist', schema='anatel')
    op.create_index('idx_aerodromes_icao', 'aerodromes', ['icao'], unique=False, schema='anatel')

    op.create_table(
        'viability_studies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('service_type', sa.Text(), nullable=False),
        sa.Column('canal', sa.Text(), nullable=True),
        sa.Column('frequencia_mhz', sa.Float(), nullable=True),
        sa.Column('classe', sa.Text(), nullable=True),
        sa.Column('erp_kw', sa.Float(), nullable=True),
        sa.Column('altura_antena_m', sa.Float(), nullable=True),
        sa.Column('haat_m', sa.Float(), nullable=True),
        sa.Column('polarizacao', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('municipio', sa.Text(), nullable=True),
        sa.Column('uf', sa.Text(), nullable=True),
        sa.Column('parametros_json', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('resultado_json', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='anatel',
    )


def downgrade():
    op.drop_table('viability_studies', schema='anatel')
    op.drop_index('idx_aerodromes_icao', table_name='aerodromes', schema='anatel')
    op.drop_index('idx_aerodromes_geom', table_name='aerodromes', schema='anatel')
    op.drop_table('aerodromes', schema='anatel')
    op.drop_index('idx_anatel_stations_service', table_name='anatel_stations', schema='anatel')
    op.drop_index('idx_anatel_stations_geom', table_name='anatel_stations', schema='anatel')
    op.drop_table('anatel_stations', schema='anatel')
