from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables.

    Values are read from the environment (and an optional local .env file).
    No secrets should ever be committed; see services/api/.env.example.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Veyra API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://veyra:veyra@localhost:5432/veyra"
    )
    # Development-only user identity. Real authentication will replace this.
    # See app/dev_user.py. Never treat this as a production identity.
    dev_user_id: str = "dev-user"
    # Comma-separated list of allowed CORS origins.
    cors_origins: str = "http://localhost:3000"


def get_settings() -> Settings:
    return Settings()