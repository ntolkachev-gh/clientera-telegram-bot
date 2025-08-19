#!/usr/bin/env python3
"""
Скрипт для тестирования работы с GPT-5
"""
import asyncio
import os
from dotenv import load_dotenv
from core.openai_client import OpenAIClient
from database.database import SessionLocal

# Загружаем переменные окружения
load_dotenv()

async def test_gpt5():
    """Тестируем работу с GPT-5"""
    print("🧪 Тестирование GPT-5...")

    # Проверяем настройки
    api_key = os.getenv("OPENAI_API_KEY")
    default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-5")

    if not api_key:
        print("❌ OPENAI_API_KEY не найден в переменных окружения")
        return

    print(f"🔑 API ключ: {'*' * 10}{api_key[-4:]}")
    print(f"🤖 Модель по умолчанию: {default_model}")

    # Создаем сессию базы данных
    db = SessionLocal()

    try:
        # Создаем OpenAI клиент
        client = OpenAIClient(db)

        # Тестовое сообщение
        test_message = "Привет! Расскажи кратко о том, что ты умеешь."

        print(f"\n📝 Тестовое сообщение: {test_message}")
        print("⏳ Отправляем запрос...")

        # Отправляем запрос
        response = await client.chat_completion(
            messages=[{"role": "user", "content": test_message}],
            client_id=None
        )

        print(f"\n✅ Ответ получен:")
        print(f"📤 {response}")

        # Проверяем, какая модель была использована
        print(f"\n🔍 Проверяем логи использования...")

        # Получаем последний лог использования
        from database.models import OpenAIUsageLog
        latest_usage = db.query(OpenAIUsageLog).order_by(OpenAIUsageLog.id.desc()).first()

        if latest_usage:
            print(f"📊 Последнее использование:")
            print(f"   Модель: {latest_usage.model}")
            print(f"   Токены: {latest_usage.total_tokens}")
            print(f"   Стоимость: ${latest_usage.cost_usd:.4f}")
            print(f"   Цель: {latest_usage.purpose}")
        else:
            print("❌ Логи использования не найдены")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_gpt5())
