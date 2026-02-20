"""fix price_display_mode: convert from pg enum to varchar with lowercase values

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-20 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Проверяем тип колонки — если уже VARCHAR, пропускаем конвертацию
    result = conn.execute(sa.text("""
        SELECT data_type FROM information_schema.columns
        WHERE table_name='ai_models' AND column_name='price_display_mode'
    """)).fetchone()

    if result and result[0] != 'character varying':
        # Колонка — PostgreSQL enum, конвертируем в VARCHAR
        conn.execute(sa.text("""
            ALTER TABLE ai_models
                ALTER COLUMN price_display_mode TYPE VARCHAR(50)
                USING price_display_mode::TEXT
        """))

    # Приводим все значения к lowercase (на случай если были uppercase)
    conn.execute(sa.text("""
        UPDATE ai_models
        SET price_display_mode = LOWER(price_display_mode)
        WHERE price_display_mode != LOWER(price_display_mode)
    """))

    # Дропаем старый PostgreSQL enum тип если остался
    conn.execute(sa.text("DROP TYPE IF EXISTS pricedisplaymode"))


def downgrade() -> None:
    conn = op.get_bind()

    # При откате просто оставляем VARCHAR — это безопасно
    pass
