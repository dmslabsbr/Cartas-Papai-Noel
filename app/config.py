from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables (.env)."""
    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(alias="DATABASE_URL")
    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_bucket: str = Field(default="cartas", alias="MINIO_BUCKET")
    # Credenciais MinIO (opcionais; use um dos pares abaixo)
    minio_access_key: Optional[str] = Field(default=None, alias="MINIO_ACCESS_KEY")
    minio_secret_key: Optional[str] = Field(default=None, alias="MINIO_SECRET_KEY")
    minio_root_user: Optional[str] = Field(default=None, alias="MINIO_ROOT_USER")
    minio_root_password: Optional[str] = Field(default=None, alias="MINIO_ROOT_PASSWORD")
    app_port: int = Field(default=8000, alias="APP_PORT")
    
    # Configurações de autenticação
    ldap_api_url: str = Field(default="http://auth-api.example.com", alias="LDAP_API_URL")
    session_secret_key: str = Field(default="insecure_key_for_dev_only", alias="SESSION_SECRET_KEY")
    session_max_age: int = Field(default=86400, alias="SESSION_MAX_AGE")  # 24 horas em segundos

    # pydantic-settings v2 style config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

def get_settings() -> "Settings":
    return Settings()  # type: ignore[call-arg]
