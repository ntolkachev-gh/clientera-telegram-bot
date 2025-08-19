#!/usr/bin/env python3
"""
Тестирование поиска в базе знаний Qdrant
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


async def test_search():
    """Тестирование поиска в базе знаний"""
    try:
        logger.info("🔍 Тестируем поиск в базе знаний...")

        embedding_service = EmbeddingService()

        # Тестовые запросы
        test_queries = [
            "маникюр цены",
            "запись к мастеру",
            "услуги салона",
            "контакты телефон",
            "Севиль мастер"
        ]

        all_working = True

        for query in test_queries:
            try:
                logger.info(f"🔎 Тестируем запрос: '{query}'")
                results = await embedding_service.search_similar(query, limit=2)

                if results:
                    logger.info(f"✅ Найдено {len(results)} результатов:")
                    for i, result in enumerate(results, 1):
                        title = result.payload.get('title', 'Без названия')
                        score = result.score
                        category = result.payload.get('category', 'unknown')
                        logger.info(f"  {i}. {title} (релевантность: {score:.3f}, категория: {category})")
                else:
                    logger.warning(f"⚠️ По запросу '{query}' ничего не найдено")
                    all_working = False

            except Exception as e:
                logger.error(f"❌ Ошибка при поиске '{query}': {e}")
                all_working = False

        if all_working:
            logger.info("🎉 Все тесты поиска прошли успешно!")
            return True
        else:
            logger.warning("⚠️ Некоторые тесты не прошли")
            return False

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при тестировании: {e}")
        return False


async def check_collection_status():
    """Проверка статуса коллекции"""
    try:
        logger.info("📊 Проверяем статус коллекции...")

        embedding_service = EmbeddingService()

        # Получаем список коллекций
        collections = embedding_service.qdrant_client.get_collections()
        logger.info(f"📋 Всего коллекций в Qdrant: {len(collections.collections)}")

        # Ищем нашу коллекцию
        our_collection = None
        for collection in collections.collections:
            logger.info(f"  - {collection.name}")
            if collection.name == "laliq_knowledge_base":
                our_collection = collection

        if our_collection:
            logger.info("✅ Коллекция laliq_knowledge_base найдена!")
            return True
        else:
            logger.error("❌ Коллекция laliq_knowledge_base не найдена!")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке коллекций: {e}")
        return False


async def main():
    """Основная функция"""
    print("🧪 Тестирование базы знаний Qdrant")
    print("=" * 40)

    # Проверяем конфигурацию
    logger.info(f"🔧 Qdrant URL: {settings.qdrant_url}")

    # Проверяем статус коллекции
    collection_ok = await check_collection_status()
    if not collection_ok:
        print("\n❌ Коллекция не найдена!")
        return

    # Тестируем поиск
    search_ok = await test_search()

    print("\n" + "=" * 40)
    if search_ok:
        print("🎉 База знаний работает корректно!")
        print("🤖 Бот готов отвечать на вопросы пользователей.")
    else:
        print("⚠️ Обнаружены проблемы с поиском.")
        print("🔍 Проверьте логи выше для деталей.")
    print("=" * 40)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
