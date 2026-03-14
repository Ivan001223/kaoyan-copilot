import logging
import os
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class LLMConfig(BaseSettings):
    api_key: str = Field(default="", alias="LLM_API_KEY")
    base_url: str = Field(default="https://api.moonshot.cn/v1", alias="LLM_BASE_URL")
    model: str = Field(default="kimi-k2-turbo-preview", alias="LLM_MODEL")


class RadarConfig(BaseSettings):
    enabled: bool = Field(default=True, alias="RADAR_ENABLED")
    schedule_time: str = Field(default="08:00", alias="RADAR_SCHEDULE_TIME")
    target_school: str = Field(default="东南大学", alias="RADAR_TARGET_SCHOOL")


class PoliticsConfig(BaseSettings):
    enabled: bool = Field(default=True, alias="POLITICS_ENABLED")
    schedule_time: str = Field(default="08:00", alias="POLITICS_SCHEDULE_TIME")


class DatabaseConfig(BaseSettings):
    type: str = Field(default="mysql", alias="DB_TYPE")
    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=3306, alias="DB_PORT")
    user: str = Field(default="root", alias="DB_USER")
    password: str = Field(default="password", alias="DB_PASSWORD")
    db_name: str = Field(default="kaoyan_copilot", alias="DB_NAME")


class GeneralConfig(BaseSettings):
    exam_date: str = Field(default="2026-12-20", alias="EXAM_DATE")


class EmbeddingsConfig(BaseSettings):
    provider: str = Field(default="modelscope", alias="EMBEDDINGS_PROVIDER")
    model_name: str = Field(default="", alias="EMBEDDINGS_MODEL_NAME")
    model_path: str = Field(default="", alias="MODEL_PATH_EMBEDDING")
    device: str = "auto"
    batch_size: int = 32
    normalize: bool = True


class RerankerConfig(BaseSettings):
    provider: str = Field(default="modelscope", alias="RERANKER_PROVIDER")
    model_name: str = Field(default="", alias="RERANKER_MODEL_NAME")
    model_path: str = Field(default="", alias="MODEL_PATH_RERANKER")
    device: str = "auto"


class SearchConfig(BaseSettings):
    provider: str = Field(default="duckduckgo", alias="SEARCH_PROVIDER")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")


class StorageLocalConfig(BaseSettings):
    documents_dir: str = "data/documents"
    uploads_dir: str = "data/uploads"


class AuthConfig(BaseSettings):
    secret_key: str = Field(default="set-secret-key-before-production", alias="AUTH_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="AUTH_ALGORITHM")
    access_token_expire_minutes: int = 60


class FeatureFlagsConfig(BaseSettings):
    enable_docs_rag: bool = Field(default=True, alias="ENABLE_DOCS_RAG")
    enable_chat_memory: bool = Field(default=True, alias="ENABLE_CHAT_MEMORY")
    enable_self_correction: bool = Field(default=True, alias="ENABLE_SELF_CORRECTION")
    enable_human_approval: bool = False


class ServerConfig(BaseSettings):
    host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    port: int = Field(default=8000, alias="SERVER_PORT")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    radar: RadarConfig = Field(default_factory=RadarConfig)
    politics: PoliticsConfig = Field(default_factory=PoliticsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    storage_local: StorageLocalConfig = Field(default_factory=StorageLocalConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    feature_flags: FeatureFlagsConfig = Field(default_factory=FeatureFlagsConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    def get(self, path: str, default: Any = None) -> Any:
        keys = path.split(".")
        obj = self
        for key in keys:
            if hasattr(obj, key):
                obj = getattr(obj, key)
            else:
                return default
        return obj


settings = Settings()
