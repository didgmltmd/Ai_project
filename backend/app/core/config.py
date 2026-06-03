from functools import lru_cache
import json
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PushForm AI Backend"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    base_dir: Path = Path(__file__).resolve().parents[2]
    upload_dir_name: str = Field(default="uploads", alias="UPLOAD_DIR")
    results_dir_name: str = Field(default="results", alias="RESULT_DIR")
    shortforms_dir_name: str = Field(default="shortforms", alias="SHORTFORM_DIR")
    database_file_name: str = Field(default="pushup_ai.sqlite3", alias="DATABASE_FILE")
    database_url: str = Field(
        default="postgresql+asyncpg://pushform:pushform_password@db:5432/pushform",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    postgres_db: str = Field(default="pushform", alias="POSTGRES_DB")
    postgres_user: str = Field(default="pushform", alias="POSTGRES_USER")
    postgres_password: str = Field(default="pushform_password", alias="POSTGRES_PASSWORD")
    yolo_pose_model: str = Field(default="yolov8n-pose.pt", alias="YOLO_MODEL_PATH")
    yolo_conf: float = Field(default=0.6, alias="YOLO_CONF")
    sample_fps: int = 5
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("CORS_ORIGINS", "ALLOWED_ORIGINS", "cors_origins"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def uploads_dir(self) -> Path:
        path = self.base_dir / self.upload_dir_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def results_dir(self) -> Path:
        path = self.base_dir / self.results_dir_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def shortforms_dir(self) -> Path:
        path = self.base_dir / self.shortforms_dir_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def database_path(self) -> Path:
        path = self.base_dir / self.database_file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
