from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
import os


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ai_me642.sqlite3")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    upload_root: Path = Path(os.getenv("UPLOAD_ROOT", "data/uploads"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    cors_origins_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    allowed_extensions: set[str] = {
        ".in",
        ".log",
        ".txt",
        ".md",
        ".py",
        ".sh",
        ".slurm",
        ".sbatch",
        ".ipynb",
        ".png",
        ".jpg",
        ".jpeg",
        ".csv",
        ".dat",
        ".json",
        ".pdf",
    }

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_root.mkdir(parents=True, exist_ok=True)
    return settings
