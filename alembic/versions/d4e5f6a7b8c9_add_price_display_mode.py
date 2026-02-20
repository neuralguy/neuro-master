"""add price_display_mode to ai_models

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-20 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('ai_models', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'price_display_mode',
                sa.String(50),
                nullable=False,
                server_default='fixed',
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('ai_models', schema=None) as batch_op:
        batch_op.drop_column('price_display_mode')
