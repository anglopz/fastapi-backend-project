from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


_base_config = SettingsConfigDict(
    env_file="./.env",
    env_ignore_empty=True,
    extra="ignore",
)


class AppSettings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "FastShip"
    APP_DOMAIN: str = "localhost:8000"

    model_config = _base_config


class SecuritySettings(BaseSettings):
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    model_config = _base_config


class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "fastapi_db"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"

    model_config = _base_config

    @property
    def POSTGRES_URL(self) -> str:
        """Return a Postgres async URL.
        
        PostgreSQL is now required (no SQLite fallback).
        Uses default values if not set in environment.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


class MailSettings(BaseSettings):
    """Mail/Email notification settings"""
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "FastShip"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    model_config = _base_config


class TwilioSettings(BaseSettings):
    """Twilio SMS notification settings"""
    TWILIO_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_NUMBER: str = ""

    model_config = _base_config


# New naming convention (db_settings, security_settings)
app_settings = AppSettings()
db_settings = DatabaseSettings()
security_settings = SecuritySettings()
mail_settings = MailSettings()
twilio_settings = TwilioSettings()

# Migration wrapper for backward compatibility
# TODO: Remove this after all code is migrated to use db_settings
settings = db_settings
