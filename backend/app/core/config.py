from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DATABASE_URL = "sqlite:///./runtime/agrisage.db"


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or `.env`."""

    app_name: str = Field(default="AgriSage AI", validation_alias="APP_NAME")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    seed_data: bool = Field(default=True, validation_alias="SEED_DATA")

    # Structured risk scoring remains deterministic and independent of this model.
    model_provider: str = Field(default="ollama", validation_alias="MODEL_PROVIDER")
    model_name: str = Field(default="qwen3:1.7b", validation_alias="MODEL_NAME")
    model_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("MODEL_BASE_URL", "OLLAMA_BASE_URL"),
    )
    model_api_key: str = Field(default="", validation_alias="MODEL_API_KEY")
    model_timeout_seconds: float = Field(default=180, validation_alias="MODEL_TIMEOUT_SECONDS")

    # The public reference page is optional evidence; a fetch failure is logged and
    # never substituted with invented content.
    external_evidence_url: str = Field(
        default="https://www.fao.org/policy-support/policy-themes/climate-smart-agriculture/Understanding-climate-smart-agriculture-/en",
        validation_alias="EXTERNAL_EVIDENCE_URL",
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        """Use local SQLite only when the deployment has not supplied a URL."""

        return (self.database_url or "").strip() or LOCAL_DATABASE_URL

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
