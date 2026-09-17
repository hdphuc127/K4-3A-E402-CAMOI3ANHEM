from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MistakeTutor API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    backend_cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    )
    database_url: str = "sqlite:///./storage/mistaketutor.db"
    auth_secret_key: str = "change-me-in-local-env"
    auth_token_expire_minutes: int = 1440

feat/core-apis
    llm_provider: str = "openai"
    default_llm_model: str = "gpt-4o-mini"
=======
main
    gemini_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    llm_primary_provider: str = "gemini"
    llm_fallback_provider: str = "openai"
    llm_deadline_s: float = 10.0
    enable_llm_judge: bool = False
feat/core-apis
    qdrant_url: str = "http://127.0.0.1:6663"
    qdrant_sources_collection: str = "mistaketutor_sources"
    embedding_dim: int = 1536
    embedding_provider: str = "openai"
    openai_embedding_model: str = "text-embedding-3-small"
=======
main

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def sqlite_path(self) -> str:
        if not self.database_url.startswith("sqlite:///"):
            msg = "Only sqlite:/// database URLs are supported by this scaffold."
            raise ValueError(msg)
        return self.database_url.replace("sqlite:///", "", 1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
