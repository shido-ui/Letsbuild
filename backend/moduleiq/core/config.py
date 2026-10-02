from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ModuleIQ"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/moduleiq.db"
    data_dir: str = "./data"
    storage_root: str = "./data/storage"
    max_upload_bytes: int = 250 * 1024 * 1024
    allowed_media_types: list[str] = ["application/pdf"]
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
