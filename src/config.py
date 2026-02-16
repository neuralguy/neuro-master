from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Environment ===
    DEV_MODE: bool = Field(default=True, description="Development mode flag")

    # === Telegram Bot ===
    BOT_TOKEN_PROD: SecretStr = Field(default="")
    BOT_TOKEN_DEV: SecretStr = Field(default="")
    ADMIN_IDS: str = Field(default="", description="Comma-separated admin Telegram IDs")
    WEBAPP_URL: str = Field(default="https://localhost:5173")

    # === Database ===
    DATABASE_URL_PROD: str = Field(
        default="postgresql+asyncpg://postgres:password@db:5432/aibot"
    )
    DATABASE_URL_DEV: str = Field(default="sqlite+aiosqlite:///./data/dev.db")

    # === Redis ===
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # === kie.ai ===
    KIE_API_KEY: SecretStr = Field(default="")
    KIE_API_URL: str = Field(default="https://api.kie.ai")

    # === poyo.ai ===
    POYO_API_KEY: SecretStr = Field(default="")
    POYO_API_URL: str = Field(default="https://api.poyo.ai")

    # === Lava.top ===
    LAVA_API_KEY: SecretStr = Field(default="", description="Lava.top API key")
    LAVA_API_URL: str = Field(default="https://gate.lava.top", description="Lava.top API base URL")
    LAVA_CURRENCY: str = Field(default="USD", description="Payment currency: RUB, USD, EUR")
    LAVA_WEBHOOK_SECRET: SecretStr = Field(default="", description="Lava.top webhook secret")

    # === Application ===
    SECRET_KEY: SecretStr = Field(default="change-me-in-production-min-32-chars")
    WELCOME_BONUS: int = Field(default=50)
    REFERRAL_BONUS: int = Field(default=50)

    # === Logging ===
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="DEBUG")
    LOG_TELEGRAM_CHAT_ID: int | None = Field(default=None)

    # === Computed Properties ===
    @computed_field
    @property
    def BOT_TOKEN(self) -> SecretStr:
        """Get bot token based on environment."""
        return self.BOT_TOKEN_DEV if self.DEV_MODE else self.BOT_TOKEN_PROD

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL based on environment."""
        return self.DATABASE_URL_DEV if self.DEV_MODE else self.DATABASE_URL_PROD



    @computed_field
    @property
    def admin_ids_list(self) -> list[int]:
        """Parse admin IDs to list of integers."""
        if not self.ADMIN_IDS:
            return []
        return [int(id_.strip()) for id_ in self.ADMIN_IDS.split(",") if id_.strip()]

    @computed_field
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.DATABASE_URL


# === Paths ===
BASE_DIR = Path(__file__).parent.parent.resolve()
SRC_DIR = BASE_DIR / "src"
STORAGE_DIR = BASE_DIR / "storage"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
for dir_path in [STORAGE_DIR, STORAGE_DIR / "generations", STORAGE_DIR / "temp", LOGS_DIR, DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
