#!/usr/bin/env python3
"""
Упрощенный тест GPT-5 без зависимости от базы данных
"""
import asyncio
import os
from dotenv import load_dotenv
import openai

# Загружаем переменные окружения
load_dotenv()

async def test_gpt5_simple():
    """Тестируем GPT-5 напрямую через OpenAI API"""
    print("🧪 Простой тест GPT-5...")

    # Проверяем настройки
    api_key = os.getenv("OPENAI_API_KEY")
    default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-5")

    if not api_key:
        print("❌ OPENAI_API_KEY не найден в переменных окружения")
        return

    print(f"🔑 API ключ: {'*' * 10}{api_key[-4:]}")
    print(f"🤖 Модель: {default_model}")

    # Создаем OpenAI клиент
    client = openai.OpenAI(api_key=api_key)

    # Тестовое сообщение
    test_message = "Привет! Расскажи кратко о том, что ты умеешь."

    print(f"\n📝 Тестовое сообщение: {test_message}")
    print("⏳ Отправляем запрос...")

    try:
        # Отправляем запрос с правильными параметрами для GPT-5
        if default_model.startswith("gpt-5"):
            response = client.chat.completions.create(
                model=default_model,
                messages=[{"role": "user", "content": test_message}]
            )
        else:
            response = client.chat.completions.create(
                model=default_model,
                messages=[{"role": "user", "content": test_message}],
                max_tokens=1000,
                temperature=0.7
            )

        # Получаем ответ
        response_content = response.choices[0].message.content
        usage = response.usage

        print(f"\n✅ Ответ получен:")
        print(f"📤 {response_content}")

        print(f"\n📊 Статистика использования:")
        print(f"   Модель: {default_model}")
        print(f"   Входные токены: {usage.prompt_tokens}")
        print(f"   Выходные токены: {usage.completion_tokens}")
        print(f"   Всего токенов: {usage.total_tokens}")

        # Примерный расчет стоимости
        if default_model.startswith("gpt-5"):
            cost = (usage.prompt_tokens * 0.005 + usage.completion_tokens * 0.015) / 1000
        else:
            cost = (usage.prompt_tokens * 0.03 + usage.completion_tokens * 0.06) / 1000

        print(f"   Примерная стоимость: ${cost:.4f}")

        print(f"\n🎉 GPT-5 работает успешно!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

        # Если GPT-5 недоступен, пробуем GPT-4
        if "gpt-5" in str(e).lower():
            print("\n🔄 Пробуем GPT-4...")
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": test_message}],
                    max_tokens=1000,
                    temperature=0.7
                )

                response_content = response.choices[0].message.content
                usage = response.usage

                print(f"\n✅ GPT-4 работает:")
                print(f"📤 {response_content}")
                print(f"📊 Токены: {usage.total_tokens}")
                print(f"💡 Рекомендация: Используйте GPT-4 или проверьте доступ к GPT-5")

            except Exception as e2:
                print(f"❌ GPT-4 тоже не работает: {e2}")

if __name__ == "__main__":
    asyncio.run(test_gpt5_simple())
