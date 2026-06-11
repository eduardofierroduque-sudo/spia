import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


def _find_env_file() -> str:
    candidates = [
        Path(".env"),
        Path("..") / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    for p in candidates:
        if p.is_file():
            return str(p.resolve())
    return ".env"


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _resolve_path(p: str) -> str:
    path = Path(p)
    if path.is_absolute():
        return str(path)
    resolved = (_PROJECT_ROOT / path).resolve()
    if resolved.exists():
        return str(resolved)
    resolved2 = path.resolve()
    if resolved2.exists():
        return str(resolved2)
    return str(resolved)


class Settings(BaseSettings):
    app_name: str = "spia"
    debug: bool = False
    database_url: str = ""
    redis_url: str = ""
    celery_broker_url: str = ""
    model_path: str = "ml/models/trained/bot_classifier.pkl"
    feature_model_path: str = "ml/models/trained/feature_scaler.pkl"
    api_rate_limit: int = 30
    max_retries: int = 3
    batch_size: int = 50
    cpp_engine_enabled: bool = False
    api_key: str = ""
    hibp_api_key: str = ""
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    scan_timeout_seconds: int = 90
    max_query_length: int = 200
    min_query_length: int = 2

    @field_validator("model_path", mode="before")
    @classmethod
    def resolve_model_path(cls, v: str) -> str:
        return _resolve_path(v)

    @field_validator("feature_model_path", mode="before")
    @classmethod
    def resolve_feature_model_path(cls, v: str) -> str:
        return _resolve_path(v)

    @field_validator("api_rate_limit", mode="before")
    @classmethod
    def clamp_rate_limit(cls, v: int) -> int:
        return max(1, min(int(v), 1000))

    @field_validator("scan_timeout_seconds", mode="before")
    @classmethod
    def clamp_timeout(cls, v: int) -> int:
        return max(10, min(int(v), 300))

    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if v and len(v) < 16:
            return secrets.token_urlsafe(32)
        return v

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def clean_origins(cls, v: str) -> str:
        if not v:
            return ""
        origins = [o.strip() for o in v.split(",") if o.strip().startswith("http")]
        return ",".join(origins)

    class Config:
        env_file = _find_env_file()
        env_prefix = "SPIA_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
