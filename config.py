import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot
    telegram_bot_token: str

    # OpenAI
    openai_api_key: str
    openai_default_model: str = "gpt-5-mini"  # Модель по умолчанию

    # Qdrant Cloud
    qdrant_url: str
    qdrant_api_key: str

    # PostgreSQL
    database_url: str

    # Youclients API
    youclients_api_key: str
    youclients_company_id: str

    # Admin settings
    admin_secret_key: str
    admin_username: str = "admin"
    admin_password: str

    # App settings
    debug: bool = False
    remind_after_days: int = 21
    session_timeout_hours: int = 6

    # OpenAI optimization settings
    openai_max_tool_calls: int = 7  # Увеличиваем до 7 для более сложных задач
    openai_request_timeout: float = 30.0  # Таймаут на запрос в секундах
    openai_connect_timeout: float = 10.0  # Таймаут на подключение в секундах

    # Model selection for speed optimization
    openai_fast_model: str = "gpt-5-mini"  # Быстрая модель для простых задач
    openai_balanced_model: str = "gpt-4o"   # Сбалансированная модель
    openai_quality_model: str = "gpt-5-mini"     # Качественная и быстрая модель
    use_fast_model_by_default: bool = True  # Использовать быструю модель по умолчанию

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
