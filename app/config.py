from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    supabase_url:str
    supabase_publishable_key:str
    supabase_secret_key:str
    database_url:str

    google_client_id:str
    google_client_secret:str
    google_refresh_token:str

    google_api_key:str
    google_api_model:str

    mistral_api_key:str
    mistral_embd_model:str

    poll_interval_seconds:int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache
def get_setting()->Settings:
    return Settings()    