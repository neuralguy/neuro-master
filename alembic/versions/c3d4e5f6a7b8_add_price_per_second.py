"""add price_per_second to ai_models

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-19 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'ai_models',
        sa.Column('price_per_second', sa.Float(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('ai_models', 'price_per_second')
