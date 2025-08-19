#!/usr/bin/env python3
"""
Скрипт для проверки текущей конфигурации OpenAI
"""
import os
from dotenv import load_dotenv
from config import settings

def check_config():
    """Проверяем текущую конфигурацию"""
    print("🔍 Проверка конфигурации OpenAI...")
    print("=" * 50)

    # Загружаем переменные окружения
    load_dotenv()

    # Проверяем API ключ
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OPENAI_API_KEY: {'*' * 10}{api_key[-4:]}")
    else:
        print("❌ OPENAI_API_KEY не найден")

    # Проверяем модель по умолчанию
    default_model = os.getenv("OPENAI_DEFAULT_MODEL")
    if default_model:
        print(f"✅ OPENAI_DEFAULT_MODEL: {default_model}")
    else:
        print(f"ℹ️ OPENAI_DEFAULT_MODEL не задан, используется: {settings.openai_default_model}")

    # Проверяем настройки из config.py
    print(f"📋 Настройки из config.py:")
    print(f"   - openai_default_model: {settings.openai_default_model}")

    # Проверяем доступность переменных
    print(f"\n🔧 Доступные переменные окружения:")
    env_vars = [
        "OPENAI_API_KEY",
        "OPENAI_DEFAULT_MODEL",
        "TELEGRAM_BOT_TOKEN",
        "QDRANT_URL",
        "DATABASE_URL"
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var or "TOKEN" in var:
                print(f"   ✅ {var}: {'*' * 10}{value[-4:]}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: не задан")

    print("\n" + "=" * 50)
    print("🎯 Рекомендации:")

    if not api_key:
        print("   1. Установите OPENAI_API_KEY в .env файле")

    if not default_model:
        print("   2. Добавьте OPENAI_DEFAULT_MODEL=gpt-5 в .env файл")

    if api_key and (default_model or settings.openai_default_model == "gpt-5"):
        print("   ✅ Конфигурация GPT-5 готова к использованию!")
        print("   🧪 Запустите: python test_gpt5.py")

if __name__ == "__main__":
    check_config()
