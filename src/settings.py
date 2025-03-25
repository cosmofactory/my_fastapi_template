from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE: str = ".env"


class EmailServiceSettings(BaseSettings):
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    SMTP_STARTTLS: bool
    SMTP_SSL_TLS: bool

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="EMAIL_", extra="ignore")


class AuthSettings(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 2
    EMAIL_VERIFICATION_EXPIRATION_HOURS: int = 24
    JWT_SECRET_KEY: str
    ALGORITHM: str

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="AUTH_", extra="ignore")


class DBSettings(BaseSettings):
    HOST: str
    PORT: str
    USER: str
    NAME: str
    PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
        )

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="DB_", extra="ignore")


class Settings(BaseSettings):
    SERVICE_NAME: str = "moi"
    ENV: Literal["prod", "demo", "test"] = "demo"
    LOGFIRE_TOKEN: str | None = None
    PROJECT_NAME: str = "Fastapi Template"

    auth: AuthSettings = AuthSettings()
    database: DBSettings = DBSettings()
    email_service: EmailServiceSettings = EmailServiceSettings()

    @property
    def VEIRIFICATION_URL(self) -> str:
        return (
            "https://google.com/auth/verify?token="
            if self.ENV == "prod"
            else "https://google.com/auth/verify?token="
        )

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()
