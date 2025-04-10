from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE: str = ".env"


class S3Settings(BaseSettings):
    ACCESS_KEY: str
    SECRET_KEY: str
    ENDPOINT_URL: str = "https://s3storage1.fra1.digitaloceanspaces.com"
    REGION: str = "fra1"
    BUCKET_NAME: str
    URL_EXPIRATION_SECONDS: int = 3600

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="S3_", extra="ignore")


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


class UploadFileSettings(BaseSettings):
    MAX_VIDEO_SIZE: int = 1024 * 1024 * 100  # 100 MB
    MAX_IMAGE_SIZE: int = 1024 * 1024 * 20  # 20 MB
    ALLOWED_IMAGE_CONTENT_TYPE: set[str] = {"image/png", "image/jpeg", "image/jpg"}
    ALLOWED_VIDEO_CONTENT_TYPE: set[str] = {"video/mp4", "video/avi", "video/mov"}
    MIN_IMAGE_DIMENSIONS: int = 300


class Settings(BaseSettings):
    SERVICE_NAME: str = "moi"
    ENV: Literal["prod", "demo", "test"] = "demo"
    LOGFIRE_TOKEN: str | None = None
    PROJECT_NAME: str = "Magician of Images"

    auth: AuthSettings = AuthSettings()
    database: DBSettings = DBSettings()
    email_service: EmailServiceSettings = EmailServiceSettings()
    s3: S3Settings = S3Settings()
    upload_file: UploadFileSettings = UploadFileSettings()

    @property
    def VEIRIFICATION_URL(self) -> str:
        return (
            "https://google.com/auth/verify?token="
            if self.ENV == "prod"
            else "https://google.com/auth/verify?token="
        )

    @property
    def COOKIE_SECURE(self) -> bool:
        return True

    @property
    def SAMESITE_VALUE(self) -> str:
        return "Lax" if self.ENV == "prod" else "None"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()
