"""应用配置，从 .env / 环境变量读取。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    database_url: str = "sqlite:///./data/ai_panel.db"


settings = Settings()
