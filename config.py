import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot
    telegram_bot_token: str
    
    # OpenAI
    openai_api_key: str
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 