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
    mineru_tier: str = "standard"
    mineru_ocr_mode: str = "auto"
    mineru_image_analysis: bool = True
    allowed_media_types: list[str] = ["application/pdf"]
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    log_level: str = "INFO"
    credential_encryption_key: str = Field("", validation_alias="MODULEIQ_CREDENTIAL_ENCRYPTION_KEY")
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_security(self):
        if self.environment.lower() not in {"development", "test"}:
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
