"""Rename yookassa columns to lava

Revision ID: a1b2c3d4e5f6
Revises: 9bfd534d9eee
Create Date: 2026-02-16 22:44:17.151899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9bfd534d9eee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename yookassa_id -> lava_id (только если колонка ещё не переименована)
    conn = op.get_bind()
    columns = [row[0] for row in conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='payments'"
    ))]
    with op.batch_alter_table('payments') as batch_op:
        if 'yookassa_id' in columns:
            batch_op.alter_column('yookassa_id', new_column_name='lava_id')
        if 'yookassa_status' in columns:
            batch_op.alter_column('yookassa_status', new_column_name='lava_status')


def downgrade() -> None:
    # Rename lava_id -> yookassa_id
    with op.batch_alter_table('payments') as batch_op:
        batch_op.alter_column('lava_id', new_column_name='yookassa_id')
        batch_op.alter_column('lava_status', new_column_name='yookassa_status')
