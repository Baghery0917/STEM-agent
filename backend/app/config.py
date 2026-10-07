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

    # 面部情绪识别服务（HTTP，POST {base_url}/recognize multipart image）
    emotion_base_url: str = ""
    emotion_api_key: str = ""
    emotion_timeout_seconds: float = 3.0

    # 教学策略服务（MCP Streamable HTTP，tool: get_teaching_strategy）
    teaching_strategy_mcp_url: str = ""
    teaching_strategy_api_key: str = ""
    teaching_strategy_timeout_seconds: float = 5.0

    # 评价处服务（MCP Streamable HTTP，tool: get_student_evaluation；自行读库，只传 student_id）
    evaluation_mcp_url: str = ""
    evaluation_api_key: str = ""
    evaluation_timeout_seconds: float = 15.0

    # 管理台登录口令（空则管理台不可登录）
    admin_password: str = ""

    # 即时情绪加权：综合 = 面部 * w + 文本 * (1 - w)
    emotion_facial_weight: float = 0.6
    # 历史情绪回流：新 = 旧 * (1 - alpha) + 本 session 均值 * alpha
    emotion_history_alpha: float = 0.3
    # 空闲自动结束：最后一条消息超过该分钟数的 active 会话自动结束并回流情绪
    teaching_idle_timeout_minutes: int = 30
    teaching_idle_sweep_interval_seconds: int = 300

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
        if self.is_production and not self.admin_password:
            raise ValueError("ADMIN_PASSWORD must be set in production")
        return self


settings = Settings()
