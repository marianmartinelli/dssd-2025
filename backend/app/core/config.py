from functools import lru_cache
from typing import List, Union

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="ProjectPlanning API")
    environment: str = Field(default="local")

    # API
    api_prefix: str = Field(default="/api/v1")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    debug: bool = Field(default=True)

    # JWT
    jwt_secret_key: str = Field(default="changeme")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expires_minutes: int = Field(default=60)

    # Database
    database_url: str = Field(default="postgresql+asyncpg://projectplanning:projectplanning@db:5432/projectplanning")

    # Bonita BPM
    bonita_base_url: str = Field(default="http://bonita:8080")
    bonita_api_username: str = Field(default="technical_user")
    bonita_api_password: str = Field(default="technical_user")
    bonita_process_definition: str = Field(default="ProjectPlanningProcess")
    bonita_process_version: str = Field(default="1.0")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
