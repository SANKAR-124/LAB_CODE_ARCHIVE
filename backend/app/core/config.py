from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    SUPER_ADMIN_SEED_USERNAME: str
    SUPER_ADMIN_SEED_EMAIL: str
    SUPER_ADMIN_SEED_PASSWORD: str


settings = Settings()