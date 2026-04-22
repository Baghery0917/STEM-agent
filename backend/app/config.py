from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/stem_db"
    database_url_sync: str = "postgresql://postgres:postgres@127.0.0.1:5432/stem_db"

    # pgvector
    pgvector_dimension: int = 1024

    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS — 逗号分隔字符串。dev 默认放开本地 Vite，生产必须显式配置
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # LLM
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_vision_model: str = ""
    llm_embedding_model: str = ""
    llm_embedding_dimension: int = 1024

    # Emotion Recognition Service
    emotion_base_url: str = ""
    emotion_api_key: str = ""

    # Teaching Strategy Service
    teaching_strategy_base_url: str = ""
    teaching_strategy_api_key: str = ""

    # Teaching: 参考题相似度阈值（>= 该值的最相似题才作为参考）
    teaching_reference_similarity_threshold: float = 0.8

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _require_prod_secrets(self) -> "Settings":
        if self.is_production and not self.llm_api_key:
            raise ValueError("LLM_API_KEY must be set in production")
        return self


settings = Settings()
