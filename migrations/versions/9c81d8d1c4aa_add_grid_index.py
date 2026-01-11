"""add grid index

Revision ID: 9c81d8d1c4aa
Revises: e2e9e951b691
Create Date: 2026-01-11 01:39:40.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '9c81d8d1c4aa'
down_revision = 'e2e9e951b691'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'idx_field_tiles_revision_layer',
        'field_tiles',
        ['revision_id', 'layer'],
        unique=False,
        schema='grid',
    )


def downgrade():
    op.drop_index('idx_field_tiles_revision_layer', table_name='field_tiles', schema='grid')
