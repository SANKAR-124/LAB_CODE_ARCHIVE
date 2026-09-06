from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    SUPER_ADMIN_SEED_USERNAME: str
    SUPER_ADMIN_SEED_EMAIL: str
    SUPER_ADMIN_SEED_PASSWORD: str


settings = Settings()