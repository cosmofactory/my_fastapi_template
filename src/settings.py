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


class MinimaxSettings(BaseSettings):
    API_KEY: str
    BASE_URL: str = "https://api.minimaxi.chat/v1/"
    GROUP_ID: str
    VIDEO_GENERATION_ENDPOINT: str = "video_generation"
    VIDEO_RETRIEVAL_ENDPOINT: str = "files/retrieve"
    VIDEO_STATUS_ENDPOINT: str = "query"
    CONTENT_TYPE: str = "application/json"
    AUTHORITY_HEADER: dict = {"authority": "api.minimaxi.chat"}
    SUCCESSFUL_STATUS: int = 0
    STATUS_CALLBACK_URL: str = "https://api-magic.avetechnologies.pro/generations/callback_url"
    DEFAULT_VIDEO_CONTENT_TYPE: str = "video/mp4"
    DEFAULT_FILE_EXTENSION: str = ".mp4"

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="MINIMAX_", extra="ignore")


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
    PROJECT_NAME: str = "Magician of Images"

    auth: AuthSettings = AuthSettings()
    database: DBSettings = DBSettings()
    email_service: EmailServiceSettings = EmailServiceSettings()
    minimax: MinimaxSettings = MinimaxSettings()
    s3: S3Settings = S3Settings()

    @property
    def VEIRIFICATION_URL(self) -> str:
        return (
            "https://google.com/auth/verify?token="
            if self.ENV == "prod"
            else "https://google.com/auth/verify?token="
        )

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()
