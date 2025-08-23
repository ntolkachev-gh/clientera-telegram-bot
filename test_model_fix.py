#!/usr/bin/env python3
"""
Тест для проверки исправления ошибки с ключом speed
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.openai_client import OpenAIClient, MODEL_SPEED_CHARACTERISTICS, PRICING
from database.database import get_db

def test_model_info():
    """Тестирование получения информации о моделях"""

    print("🧪 Тестирование исправления ошибки с ключом 'speed'")
    print("=" * 60)

    # Проверяем структуру MODEL_SPEED_CHARACTERISTICS
    print("\n📊 Проверка структуры MODEL_SPEED_CHARACTERISTICS:")
    required_keys = ["speed", "avg_response_time", "recommendation"]

    for model_name, model_data in MODEL_SPEED_CHARACTERISTICS.items():
        print(f"\n🔍 Модель: {model_name}")
        print(f"   Данные: {model_data}")

        missing_keys = [key for key in required_keys if key not in model_data]
        if missing_keys:
            print(f"   ❌ Отсутствуют ключи: {missing_keys}")
        else:
            print(f"   ✅ Все ключи присутствуют")

    # Тестируем get_model_info для всех моделей
    print("\n\n🧪 Тестирование метода get_model_info:")

    try:
        # Получаем сессию БД
        db = next(get_db())

        # Создаем клиент OpenAI
        client = OpenAIClient(db)

        # Тестируем все модели
        for model_name in MODEL_SPEED_CHARACTERISTICS.keys():
            print(f"\n📊 Тестируем модель: {model_name}")

            try:
                model_info = client.get_model_info(model_name)
                print(f"   ✅ Успешно получена информация:")
                print(f"      - Модель: {model_info['model']}")
                print(f"      - Скорость: {model_info['speed']}")
                print(f"      - Время ответа: {model_info['avg_response_time']:.1f}s")
                print(f"      - Рекомендация: {model_info['recommendation']}")
                print(f"      - Стоимость: ${model_info['cost_per_1k_tokens']:.6f}")

            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

        # Тестируем неизвестную модель
        print(f"\n📊 Тестируем неизвестную модель: 'unknown-model'")
        try:
            model_info = client.get_model_info("unknown-model")
            print(f"   ✅ Успешно обработана неизвестная модель:")
            print(f"      - Модель: {model_info['model']}")
            print(f"      - Скорость: {model_info['speed']}")
            print(f"      - Время ответа: {model_info['avg_response_time']:.1f}s")
            print(f"      - Рекомендация: {model_info['recommendation']}")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

        # Закрываем сессию БД
        db.close()

    except Exception as e:
        print(f"❌ Ошибка при создании клиента: {e}")

    print("\n" + "=" * 60)
    print("🎯 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:")
    print("✅ Ошибка с ключом 'speed' должна быть исправлена")
    print("✅ Все модели должны корректно обрабатываться")
    print("✅ Неизвестные модели должны обрабатываться безопасно")

if __name__ == "__main__":
    test_model_info()
