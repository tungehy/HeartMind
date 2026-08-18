"""HeartMind 后端配置。

所有配置均可通过环境变量 / .env 覆盖。
默认使用 SQLite，保证零依赖可跑；生产切换 PostgreSQL 只需设置 DATABASE_URL。
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 数据库：默认 SQLite（开箱即用），生产用 PostgreSQL+pgvector
    # 例：postgresql+psycopg2://heartmind:heartmind@localhost:5432/heartmind
    database_url: str = "sqlite:///./heartmind.db"

    # LLM Provider 抽象层：none=规则降级(无Key也能跑) / openai / anthropic / deepseek / local
    llm_provider: str = "none"
    llm_api_key: str = ""
    llm_base_url: str = ""          # 自定义/本地模型(OpenAI 兼容)地址
    llm_model: str = ""             # 留空则用各 provider 默认模型
    llm_temperature: float = 0.3

    # 微信导出服务（WeChatDataAnalysis）地址，可选；不配置则走"文本/JSON导入"路径
    wechat_export_url: str = ""     # 例：http://127.0.0.1:10392

    app_name: str = "HeartMind"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
