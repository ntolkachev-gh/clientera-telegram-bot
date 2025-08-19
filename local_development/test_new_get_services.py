#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования новой функции handle_get_services
"""
import asyncio
import sys
import os
from unittest.mock import AsyncMock

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

from core.openai_tools import YclientsToolsHandler
from bot.embedding import EmbeddingService


async def demo_get_services():
    """Демонстрация работы новой функции get_services"""
    print("🧪 Демонстрация новой функции handle_get_services")
    print("=" * 60)

    try:
        # Создаем реальные объекты
        embedding_service = EmbeddingService()

        # Создаем handler с реальным embedding service
        handler = YclientsToolsHandler(
            yclients_client=AsyncMock(),
            telegram_id="demo_user"
        )
        handler.embedding_service = embedding_service

        print("🔍 Получение всех услуг из Qdrant (localhost:6333)...")

        # Вызываем новую функцию
        result = await handler.handle_get_services()

        if result["success"]:
            services = result["services"]
            total_count = result["total_count"]

            print(f"✅ Успешно получено {total_count} услуг!")
            print()

            # Группируем услуги по категориям
            categories = {}
            for service in services:
                category = service["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(service)

            # Выводим услуги по категориям
            for category, category_services in categories.items():
                print(f"📋 {category} ({len(category_services)} услуг):")
                print("-" * 40)

                for service in category_services[:5]:  # Показываем первые 5 услуг
                    print(f"  • {service['title']}")
                    print(f"    💰 {service['price_display']}")
                    print(f"    ⏱️  {service['duration']} мин")
                    print()

                if len(category_services) > 5:
                    print(f"    ... и еще {len(category_services) - 5} услуг")
                    print()

            # Статистика по ценам
            prices = [s["price"] for s in services if s["price"] > 0]
            if prices:
                print("📊 Статистика по ценам:")
                print(f"  • Минимальная цена: {min(prices)} ₽")
                print(f"  • Максимальная цена: {max(prices)} ₽")
                print(f"  • Средняя цена: {sum(prices) // len(prices)} ₽")
                print()

            # Статистика по длительности
            durations = [s["duration"] for s in services]
            if durations:
                print("⏱️  Статистика по длительности:")
                print(f"  • Минимальная длительность: {min(durations)} мин")
                print(f"  • Максимальная длительность: {max(durations)} мин")
                print(f"  • Средняя длительность: {sum(durations) // len(durations)} мин")
                print()

        else:
            print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")

    except Exception as e:
        print(f"❌ Ошибка при выполнении демо: {e}")
        print("💡 Убедитесь, что:")
        print("  • Qdrant запущен на localhost:6333")
        print("  • База знаний загружена в коллекцию 'laliq_knowledge_base'")
        print("  • В коллекции есть точки с category='services'")


def test_parsing_methods():
    """Тестирование методов парсинга"""
    print("\n🧪 Тестирование методов парсинга")
    print("=" * 60)

    handler = YclientsToolsHandler(AsyncMock(), "test_user")

    # Тест парсинга услуг
    test_content = """
    # Тестовые услуги

    - Классический маникюр — 1200 ₽
    • Покрытие гель-лаком - 800 руб
    1. Френч — 1000 ₽
    Консультация: 500 ₽
    - Дизайн ногтей — 100-300 ₽
    - Окрашивание волос — 3500 ₽
    """

    services = handler._parse_services_from_content(test_content, "services_test.md")

    print(f"📋 Распарсено {len(services)} услуг:")
    for service in services:
        print(f"  • {service['title']} - {service['price_display']} ({service['duration']} мин)")

    print()

    # Тест нормализации категорий
    test_categories = [
        "services_manicure.md",
        "services_hair.md",
        "services_cosmetology.md",
        "unknown_category.md"
    ]

    print("🏷️  Тест нормализации категорий:")
    for category in test_categories:
        normalized = handler._normalize_category_name(category)
        print(f"  • {category} → {normalized}")


if __name__ == "__main__":
    print("🚀 Запуск демонстрации новой функции get_services")
    print()

    # Запускаем демо с реальным Qdrant
    asyncio.run(demo_get_services())

    # Тестируем методы парсинга
    test_parsing_methods()

    print("\n✅ Демонстрация завершена!")
    print("🧪 Для запуска полных тестов используйте: python3 -m pytest test/ -v")
