#!/usr/bin/env python3
"""
Скрипт для загрузки базы знаний в Qdrant Cloud
Используется для инициализации коллекции на Heroku или локально
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импортов
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from bot.embedding import KnowledgeBaseManager, EmbeddingService
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_qdrant_connection():
    """Проверка подключения к Qdrant"""
    try:
        logger.info("🔍 Проверяем подключение к Qdrant...")
        embedding_service = EmbeddingService()

        # Получаем список коллекций
        collections = embedding_service.qdrant_client.get_collections()
        logger.info(f"✅ Подключение успешно! Найдено коллекций: {len(collections.collections)}")

        # Проверяем нашу коллекцию
        collection_exists = any(
            collection.name == "laliq_knowledge_base"
            for collection in collections.collections
        )

        if collection_exists:
            collection_info = embedding_service.qdrant_client.get_collection("laliq_knowledge_base")
            logger.info(f"📊 Коллекция laliq_knowledge_base: {collection_info.points_count} точек")
        else:
            logger.info("❌ Коллекция laliq_knowledge_base не найдена")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Qdrant: {e}")
        return False


async def load_knowledge_base():
    """Загрузка базы знаний"""
    try:
        logger.info("🚀 Начинаем загрузку базы знаний...")

        # Проверяем наличие файлов базы знаний
        knowledge_base_path = Path("knowledge_base")
        if not knowledge_base_path.exists():
            logger.error(f"❌ Папка {knowledge_base_path} не найдена")
            return False

        md_files = list(knowledge_base_path.glob("**/*.md"))
        if not md_files:
            logger.error("❌ Markdown файлы не найдены в папке knowledge_base")
            return False

        logger.info(f"📚 Найдено {len(md_files)} файлов базы знаний")

        # Создаем менеджер базы знаний
        kb_manager = KnowledgeBaseManager()

        # Загружаем базу знаний
        await kb_manager.load_knowledge_base()

        logger.info("✅ База знаний успешно загружена!")

        # Проверяем результат
        embedding_service = EmbeddingService()
        collection_info = embedding_service.qdrant_client.get_collection("laliq_knowledge_base")
        logger.info(f"📊 Загружено {collection_info.points_count} точек в коллекцию")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке базы знаний: {e}")
        return False


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
            "контакты телефон"
        ]

        for query in test_queries:
            results = await embedding_service.search_similar(query, limit=2)
            logger.info(f"🔎 Запрос '{query}': найдено {len(results)} результатов")

            for i, result in enumerate(results, 1):
                title = result.payload.get('title', 'Без названия')
                score = result.score
                logger.info(f"  {i}. {title} (релевантность: {score:.3f})")

        logger.info("✅ Тестирование поиска завершено!")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании поиска: {e}")
        return False


async def main():
    """Основная функция"""
    print("=" * 60)
    print("🤖 LALIQ Beauty Bot - Загрузка базы знаний")
    print("=" * 60)

    # Проверяем конфигурацию
    logger.info(f"🔧 Qdrant URL: {settings.qdrant_url}")
    logger.info(f"🔧 Qdrant API Key: {'*' * 20}...{settings.qdrant_api_key[-10:] if settings.qdrant_api_key else 'НЕ УСТАНОВЛЕН'}")

    # Шаг 1: Проверка подключения
    if not await check_qdrant_connection():
        logger.error("💥 Не удалось подключиться к Qdrant. Проверьте настройки.")
        return

    # Шаг 2: Загрузка базы знаний
    if not await load_knowledge_base():
        logger.error("💥 Не удалось загрузить базу знаний.")
        return

    # Шаг 3: Тестирование
    if not await test_search():
        logger.error("💥 Тестирование поиска не удалось.")
        return

    print("\n" + "=" * 60)
    print("🎉 Загрузка базы знаний успешно завершена!")
    print("🤖 Бот готов к работе с базой знаний.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Операция прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
