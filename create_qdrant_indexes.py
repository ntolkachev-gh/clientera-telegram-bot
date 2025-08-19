#!/usr/bin/env python3
"""
Создание индексов для payload полей в коллекции Qdrant
Решает ошибку: Index required but not found for "category"
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импортов
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from bot.embedding import EmbeddingService
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_indexes():
    """Создание индексов для payload полей"""
    try:
        logger.info("🔧 Создание индексов для полей коллекции...")

        # Создаем сервис
        embedding_service = EmbeddingService()

        # Проверяем подключение
        collections = embedding_service.qdrant_client.get_collections()
        logger.info(f"✅ Подключение OK. Коллекций: {len(collections.collections)}")

        # Проверяем существование коллекции
        collection_exists = any(
            collection.name == "laliq_knowledge_base"
            for collection in collections.collections
        )

        if not collection_exists:
            logger.error("❌ Коллекция laliq_knowledge_base не найдена!")
            logger.info("💡 Сначала запустите: python load_knowledge_base.py")
            return False

        logger.info("📋 Коллекция найдена, создаем индексы...")

        # Создаем индексы
        from qdrant_client.models import PayloadSchemaType

        index_fields = [
            ("category", PayloadSchemaType.KEYWORD, "Категория контента (services, specialists, etc.)"),
            ("specialist", PayloadSchemaType.KEYWORD, "Специалист (sevil_bammatova, jamila_hunkaeva, etc.)"),
            ("has_prices", PayloadSchemaType.BOOL, "Наличие цен в контенте"),
            ("filename", PayloadSchemaType.KEYWORD, "Имя исходного файла"),
            ("language", PayloadSchemaType.KEYWORD, "Язык контента (ru)")
        ]

        created_count = 0
        existing_count = 0

        for field_name, field_type, description in index_fields:
            try:
                embedding_service.qdrant_client.create_payload_index(
                    collection_name="laliq_knowledge_base",
                    field_name=field_name,
                    field_schema=field_type
                )
                logger.info(f"✅ Создан индекс для поля '{field_name}' - {description}")
                created_count += 1

            except Exception as e:
                if "already exists" in str(e).lower() or "index already exists" in str(e).lower():
                    logger.info(f"ℹ️ Индекс для поля '{field_name}' уже существует")
                    existing_count += 1
                else:
                    logger.warning(f"⚠️ Не удалось создать индекс для '{field_name}': {e}")

        logger.info(f"📊 Результат: создано {created_count}, уже существовало {existing_count}")

        if created_count > 0:
            logger.info("🎉 Новые индексы созданы успешно!")

        logger.info("✅ Теперь фильтры в openai_tools должны работать корректно")
        return True

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False


async def test_indexes():
    """Тестирование работы индексов"""
    try:
        logger.info("🧪 Тестируем работу индексов...")

        embedding_service = EmbeddingService()

        # Тестируем фильтр по категории (как в openai_tools)
        scroll_result = embedding_service.qdrant_client.scroll(
            collection_name="laliq_knowledge_base",
            scroll_filter={
                "must": [
                    {"key": "category", "match": {"value": "services"}}
                ]
            },
            limit=5,
            with_payload=True,
            with_vectors=False
        )

        points = scroll_result[0]
        logger.info(f"✅ Фильтр по category='services' работает! Найдено {len(points)} записей")

        if points:
            for i, point in enumerate(points[:2], 1):
                title = point.payload.get('title', 'Без названия')
                category = point.payload.get('category', 'unknown')
                logger.info(f"  {i}. {title} (категория: {category})")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return False


async def main():
    """Основная функция"""
    print("🔧 Создание индексов для Qdrant коллекции")
    print("=" * 50)

    # Проверяем конфигурацию
    logger.info(f"🔧 Qdrant URL: {settings.qdrant_url}")

    # Создаем индексы
    success = await create_indexes()
    if not success:
        print("\n❌ Создание индексов не удалось!")
        return

    # Тестируем индексы
    test_success = await test_indexes()

    print("\n" + "=" * 50)
    if success and test_success:
        print("🎉 Индексы созданы и работают корректно!")
        print("🤖 Теперь openai_tools должны работать без ошибок.")
        print("💡 Попробуйте спросить у бота: 'Какие у вас услуги?'")
    else:
        print("⚠️ Обнаружены проблемы с индексами.")
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Создание индексов прервано пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
