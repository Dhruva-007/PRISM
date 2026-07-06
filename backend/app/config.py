"""
Application configuration module.

Loads and validates all environment variables using Pydantic Settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PRISM"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False

    google_cloud_project_id: str = ""
    google_cloud_location: str = "us-central1"

    vertex_ai_model_id: str = "gemini-2.5-flash"

    firebase_service_account_path: str = "firebase-service-account.json"

    allowed_origins: str = "http://localhost:3000"

    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",")]
        clean = []
        for o in origins:
            if o:
                clean.append(o)
        return clean

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()