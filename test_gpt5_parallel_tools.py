"""
Тест для проверки GPT-5 с parallel tool calling
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal
from core.openai_client import OpenAIClient
from core.yclients_client import YclientsClient
from config import settings


async def test_gpt5_parallel():
    """Тест GPT-5 с parallel tool calling"""
    print("🚀 Тестируем GPT-5 с parallel tool calling...")

    # Создаем сессию БД
    db = SessionLocal()

    try:
        # Создаем клиенты
        yclients_client = YclientsClient(
            api_key=settings.youclients_api_key,
            company_id=settings.youclients_company_id
        )

        openai_client = OpenAIClient(db=db, yclients_client=yclients_client)

        print(f"📋 Используемая модель: {settings.openai_default_model}")
        print(f"🔧 Доступно tools: {len(openai_client.available_tools)}")

        # Тестовое сообщение, которое должно вызвать несколько tools параллельно
        messages = [
            {
                "role": "system",
                "content": "Ты ассистент салона красоты. Помогаешь клиентам с записью на услуги."
            },
            {
                "role": "user",
                "content": "Покажи мне список услуг и мастеров салона"
            }
        ]

        print("📞 Отправляем запрос с возможностью parallel tool calling...")

        # Засекаем время
        import time
        start_time = time.time()

        response = await openai_client.chat_completion_with_tools(
            messages=messages,
            client_id=None,
            model=settings.openai_default_model
        )

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"⏱️ Время выполнения: {execution_time:.2f} секунд")
        print(f"📋 Ответ модели: {response[:300]}...")

        # Тест с более сложным запросом
        print("\n🔄 Тестируем сложный запрос...")

        complex_messages = [
            {
                "role": "system",
                "content": "Ты ассистент салона красоты. Помогаешь клиентам с записью на услуги."
            },
            {
                "role": "user",
                "content": "Найди услугу маникюр, покажи мастера Севиль и доступные слоты на завтра"
            }
        ]

        start_time = time.time()

        complex_response = await openai_client.chat_completion_with_tools(
            messages=complex_messages,
            client_id=None,
            model=settings.openai_default_model
        )

        end_time = time.time()
        complex_execution_time = end_time - start_time

        print(f"⏱️ Время выполнения сложного запроса: {complex_execution_time:.2f} секунд")
        print(f"📋 Ответ на сложный запрос: {complex_response[:300]}...")

        print("✅ Тест завершен успешно!")

    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_gpt5_parallel())
