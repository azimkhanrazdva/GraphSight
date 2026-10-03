from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GRAPHSIGHT_", env_file=".env")

    env: str = "development"
    storage_dir: Path = Path(".graphsight-storage")
    max_upload_mb: int = 20
    max_image_pixels: int = 12_000_000
    cors_origins: str = "http://localhost:3000"

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

