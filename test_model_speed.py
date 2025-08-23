#!/usr/bin/env python3
"""
Скрипт для тестирования скорости разных моделей OpenAI
"""

import asyncio
import time
from datetime import datetime
from core.openai_client import OpenAIClient
from database.database import get_db
from config import settings

async def test_model_speed():
    """Тестирование скорости разных моделей"""

    # Получаем сессию БД
    db = next(get_db())

    # Создаем клиент OpenAI
    client = OpenAIClient(db)

    # Тестовое сообщение
    test_message = "Привет! Хочу записаться на маникюр завтра вечером"

    # Модели для тестирования
    models_to_test = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-5"
    ]

    print("🚀 Тестирование скорости моделей OpenAI")
    print("=" * 50)

    for model in models_to_test:
        print(f"\n📊 Тестируем модель: {model}")

        try:
            # Засекаем время
            start_time = time.time()

            # Тестируем простой запрос
            response = await client.chat_completion(
                messages=[{"role": "user", "content": test_message}],
                model=model
            )

            end_time = time.time()
            response_time = end_time - start_time

            # Получаем информацию о модели
            model_info = client.get_model_info(model)

            print(f"✅ Ответ получен за {response_time:.2f} секунд")
            print(f"📝 Длина ответа: {len(response)} символов")
            print(f"⚡ Характеристики: {model_info['speed']} | Ожидалось: {model_info['avg_response_time']:.1f}s")
            print(f"💰 Стоимость за 1K токенов: ${model_info['cost_per_1k_tokens']:.6f}")

            # Оценка производительности
            if response_time < 5:
                performance = "🚀 ОТЛИЧНО"
            elif response_time < 10:
                performance = "✅ ХОРОШО"
            elif response_time < 20:
                performance = "⚠️ МЕДЛЕННО"
            else:
                performance = "🐌 ОЧЕНЬ МЕДЛЕННО"

            print(f"📊 Оценка: {performance}")

        except Exception as e:
            print(f"❌ Ошибка при тестировании {model}: {e}")

    print("\n" + "=" * 50)
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("• GPT-4o-mini: Для максимальной скорости")
    print("• GPT-4o: Для баланса скорости и качества")
    print("• GPT-5: Только для сложных аналитических задач")

    # Закрываем сессию БД
    db.close()

if __name__ == "__main__":
    asyncio.run(test_model_speed())
