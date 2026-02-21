from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./at_user.db"
    clerk_jwks_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
