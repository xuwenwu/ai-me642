from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
import os


DEVELOPMENT_SECRET = "dev-secret-change-me"
PRODUCTION_SECRET_PLACEHOLDER = "replace-with-at-least-32-random-characters"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ai_me642.sqlite3")
    secret_key: str = os.getenv("SECRET_KEY", DEVELOPMENT_SECRET)
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    upload_root: Path = Path(os.getenv("UPLOAD_ROOT", "data/uploads"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    cors_origins_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    seed_demo_data: bool = _env_bool("SEED_DEMO_DATA", True)
    ai_provider_enabled: bool = _env_bool("AI_PROVIDER_ENABLED", False)
    ai_provider_mode: str = os.getenv("AI_PROVIDER_MODE", "offline")
    ai_provider_model: str = os.getenv("AI_PROVIDER_MODEL", "gpt-5.5-mini")
    ai_max_prompt_chars: int = int(os.getenv("AI_MAX_PROMPT_CHARS", "6000"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
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

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}


def validate_runtime_security(settings: Settings) -> None:
    if not settings.is_production:
        return
    errors: list[str] = []
    if (
        settings.secret_key in {DEVELOPMENT_SECRET, PRODUCTION_SECRET_PLACEHOLDER}
        or len(settings.secret_key) < 32
    ):
        errors.append("SECRET_KEY must be changed to a strong production value.")
    if settings.seed_demo_data:
        errors.append("SEED_DEMO_DATA must be false in production.")
    if any(origin == "*" for origin in settings.cors_origins):
        errors.append("CORS_ORIGINS must not include '*' in production.")
    if settings.ai_provider_enabled and settings.ai_provider_mode == "openai" and not settings.openai_api_key:
        errors.append("OPENAI_API_KEY must be set when OpenAI provider calls are enabled.")
    if errors:
        raise RuntimeError("Production configuration is not safe: " + " ".join(errors))


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_root.mkdir(parents=True, exist_ok=True)
    return settings
