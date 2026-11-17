"""归一 · 配置。所有可调参数集中在这里，环境变量覆盖默认值。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "onefold"
    env: str = "dev"

    # 存储
    database_url: str = "sqlite:///./onefold.db"
    data_dir: Path = Path("./data")
    max_upload_mb: int = 20

    # 鉴权
    jwt_secret: str = "change-me-in-env"
    jwt_ttl_hours: int = 24
    cookie_secure: bool = False

    # 模型（DeepSeek）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 嵌入 / 重排（家里 4080 Infinity）
    embed_base_url: str = "http://127.0.0.1:7997"
    embed_model: str = "BAAI/bge-m3"
    rerank_base_url: str = "http://127.0.0.1:7997"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"

    # 并发与队列
    global_concurrency: int = 8
    per_user_concurrency: int = 1
    queue_timeout_s: int = 60

    # 配额（每日）
    guest_messages_per_day: int = 10
    user_messages_per_day: int = 100
    guest_docs_max: int = 1
    user_docs_max: int = 20

    # 上下文预算（token）
    context_system: int = 2000
    context_tools: int = 2000
    context_memory: int = 1000
    context_rag: int = 4000
    context_history: int = 8000
    context_output: int = 4000


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
