"""fix price_display_mode enum values to lowercase

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

    # Проверяем какие значения сейчас в колонке
    # и конвертируем uppercase → lowercase если нужно
    conn.execute(sa.text("""
        ALTER TABLE ai_models
            ALTER COLUMN price_display_mode TYPE VARCHAR(50)
    """))

    # Приводим существующие значения к lowercase
    conn.execute(sa.text("""
        UPDATE ai_models
        SET price_display_mode = LOWER(price_display_mode)
    """))

    # Дропаем старый enum тип
    conn.execute(sa.text("DROP TYPE IF EXISTS pricedisplaymode"))

    # Создаём новый enum с lowercase значениями
    conn.execute(sa.text("""
        CREATE TYPE pricedisplaymode AS ENUM ('per_second', 'fixed')
    """))

    # Переключаем колонку обратно на enum
    conn.execute(sa.text("""
        ALTER TABLE ai_models
            ALTER COLUMN price_display_mode TYPE pricedisplaymode
            USING price_display_mode::pricedisplaymode
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        ALTER TABLE ai_models
            ALTER COLUMN price_display_mode TYPE VARCHAR(50)
    """))

    conn.execute(sa.text("""
        UPDATE ai_models
        SET price_display_mode = UPPER(price_display_mode)
    """))

    conn.execute(sa.text("DROP TYPE IF EXISTS pricedisplaymode"))

    conn.execute(sa.text("""
        CREATE TYPE pricedisplaymode AS ENUM ('PER_SECOND', 'FIXED')
    """))

    conn.execute(sa.text("""
        ALTER TABLE ai_models
            ALTER COLUMN price_display_mode TYPE pricedisplaymode
            USING price_display_mode::pricedisplaymode
    """))
