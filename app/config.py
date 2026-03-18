from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = APP_DIR / "uploads"
DB_PATH = BASE_DIR / "tone_copier.db"


class Settings(BaseSettings):
    app_name: str = "Quad Cortex Tone Copy Assistant"
    debug: bool = False
    max_upload_size_mb: int = 25
    allowed_extensions: tuple[str, ...] = (
        ".wav",
        ".mp3",
        ".flac",
        ".m4a",
        ".aac",
        ".ogg",
    )
    sample_rate: int = 22050
    upload_dir: Path = Field(default=UPLOAD_DIR)
    data_dir: Path = Field(default=DATA_DIR)
    database_url: str = f"sqlite:///{DB_PATH}"
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    model_config = SettingsConfigDict(env_prefix="TONE_APP_", env_file=".env", extra="ignore")


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)
