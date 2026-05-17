from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Supabase (database only)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # Firebase Admin SDK credentials
    firebase_project_id: str = ""
    firebase_private_key_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    firebase_client_id: str = ""
    firebase_auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    firebase_token_uri: str = "https://oauth2.googleapis.com/token"

    # AI Providers
    groq_api_key: str = ""
    anthropic_api_key: str = ""

    # Scraper Settings
    scrape_interval_hours: int = 6
    min_salary: int = 0

    # Dev Auth
    allow_dev_auth: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS - comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
