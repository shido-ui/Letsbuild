from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ModuleIQ"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/moduleiq.db"
    data_dir: str = "./data"
    storage_root: str = "./data/storage"
    max_upload_bytes: int = 250 * 1024 * 1024
    max_request_bytes: int = 260 * 1024 * 1024
    rate_limit_per_minute: int = 120
    auth_rate_limit_per_minute: int = 15
    max_pdf_pages: int = 10000
    mineru_tier: str = "standard"
    mineru_ocr_mode: str = "auto"
    mineru_image_analysis: bool = True
    allowed_media_types: list[str] = ["application/pdf"]
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost", "http://127.0.0.1"]
    log_level: str = "INFO"
    credential_encryption_key: str = Field("", validation_alias="MODULEIQ_CREDENTIAL_ENCRYPTION_KEY")
    secret_key: str = Field("moduleiq-development-secret-change-me", validation_alias="MODULEIQ_SECRET_KEY")
    access_token_expire_minutes: int = Field(60, validation_alias="MODULEIQ_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_algorithm: str = "HS256"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_security(self):
        if self.environment.lower() not in {"development", "test"}:
            if not self.secret_key:
                raise ValueError("MODULEIQ_SECRET_KEY is required outside development/test")
            if len(self.secret_key) < 32:
                raise ValueError("MODULEIQ_SECRET_KEY must be at least 32 characters")
            if self.access_token_expire_minutes < 5 or self.access_token_expire_minutes > 1440:
                raise ValueError("MODULEIQ_ACCESS_TOKEN_EXPIRE_MINUTES must be between 5 and 1440")
            if not self.credential_encryption_key:
                raise ValueError("MODULEIQ_CREDENTIAL_ENCRYPTION_KEY is required outside development/test")
            if not self.cors_origins:
                raise ValueError("CORS origins must be explicitly configured outside development/test")
            if not self.allowed_hosts:
                raise ValueError("Allowed hosts must be explicitly configured outside development/test")
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
