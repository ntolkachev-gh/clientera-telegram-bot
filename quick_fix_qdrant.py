#!/usr/bin/env python3
"""
Быстрое исправление Qdrant - упрощенная версия без проблемных API вызовов
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


async def quick_fix():
    """Быстрое исправление без проблемных API вызовов"""
    try:
        logger.info("🔧 Быстрое исправление Qdrant...")

        # Создаем сервис
        embedding_service = EmbeddingService()

        # Проверяем подключение
        logger.info("🔍 Проверяем подключение...")
        collections = embedding_service.qdrant_client.get_collections()
        logger.info(f"✅ Подключение OK. Коллекций: {len(collections.collections)}")

        # Проверяем существование нашей коллекции
        collection_exists = any(
            collection.name == "laliq_knowledge_base"
            for collection in collections.collections
        )

        if collection_exists:
            logger.info("📋 Коллекция laliq_knowledge_base найдена")
            logger.info("🗑️ Удаляем старую коллекцию...")
            try:
                embedding_service.qdrant_client.delete_collection("laliq_knowledge_base")
                logger.info("✅ Старая коллекция удалена")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при удалении: {e}")
        else:
            logger.info("📋 Коллекция laliq_knowledge_base не найдена")

        # Создаем новую коллекцию
        logger.info("🆕 Создаем новую коллекцию...")
        await embedding_service.init_collection()

        # Простая проверка
        collections_after = embedding_service.qdrant_client.get_collections()
        collection_exists_after = any(
            collection.name == "laliq_knowledge_base"
            for collection in collections_after.collections
        )

        if collection_exists_after:
            logger.info("✅ Коллекция успешно создана!")
            logger.info("📚 Теперь загрузите данные: python load_knowledge_base.py")
            return True
        else:
            logger.error("❌ Коллекция не была создана")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False


async def main():
    """Основная функция"""
    print("🔧 Быстрое исправление Qdrant")
    print("=" * 40)

    success = await quick_fix()

    if success:
        print("\n✅ Исправление завершено!")
        print("📚 Запустите: python load_knowledge_base.py")
    else:
        print("\n❌ Исправление не удалось!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Прервано пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
