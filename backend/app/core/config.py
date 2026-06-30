from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = "sqlite:///./bill_account.db"
    jwt_secret: str = "dev-secret-change-me-32-bytes-minimum"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    dev_code: str = "246810"
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
