from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class SecuritySettings(BaseSettings):
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def POSTGRES_URL(self) -> str:
        """Return a Postgres async URL if all Postgres settings are present.

        Falls back to a local SQLite async URL so the app can run without
        Postgres configuration during development or tests.
        """
        if (
            self.POSTGRES_SERVER
            and self.POSTGRES_USER
            and self.POSTGRES_PASSWORD
            and self.POSTGRES_DB
            and self.POSTGRES_PORT
        ):
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        # sqlite async fallback for dev/test when Postgres is not configured
        return "sqlite+aiosqlite:///./dev.db"


settings = DatabaseSettings()
security_settings = SecuritySettings()
