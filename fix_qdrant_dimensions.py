#!/usr/bin/env python3
"""
Быстрое исправление проблемы размерности векторов в Qdrant
Удаляет старую коллекцию и создает новую с правильным размером векторов
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fix_vector_dimensions():
    """Исправление размерности векторов в коллекции"""
    try:
        logger.info("🔧 Начинаем исправление размерности векторов...")

        # Создаем сервис эмбеддингов
        embedding_service = EmbeddingService()

        # Проверяем текущее состояние
        logger.info("🔍 Проверяем текущие коллекции...")
        collections = embedding_service.qdrant_client.get_collections()

        collection_exists = any(
            collection.name == "laliq_knowledge_base"
            for collection in collections.collections
        )

        if collection_exists:
            logger.info("📊 Получаем информацию о существующей коллекции...")
            try:
                collection_info = embedding_service.qdrant_client.get_collection("laliq_knowledge_base")
                # Пытаемся получить информацию о векторах и точках
                try:
                    vector_size = collection_info.config.params.vectors.size
                    points_count = collection_info.points_count

                    logger.info(f"📈 Текущая коллекция: {points_count} точек, размер векторов: {vector_size}")

                    if vector_size == 1536:
                        logger.info("✅ Размер векторов уже правильный (1536)!")
                        if points_count > 0:
                            logger.info("✅ Коллекция содержит данные, исправление не требуется")
                            return True
                        else:
                            logger.info("⚠️ Коллекция пуста, нужно загрузить данные")
                            return False

                    # Удаляем коллекцию с неправильным размером
                    logger.info(f"🗑️ Удаляем коллекцию с неправильным размером векторов ({vector_size})...")
                    embedding_service.qdrant_client.delete_collection("laliq_knowledge_base")
                    logger.info("✅ Старая коллекция удалена")

                except AttributeError as attr_error:
                    logger.warning(f"⚠️ Не удалось получить детали коллекции: {attr_error}")
                    logger.info("🗑️ Пересоздаем коллекцию из-за проблем с API...")
                    embedding_service.qdrant_client.delete_collection("laliq_knowledge_base")
                    logger.info("✅ Коллекция удалена")

            except Exception as e:
                logger.warning(f"⚠️ Ошибка при получении информации о коллекции: {e}")
                logger.info("🗑️ Пытаемся удалить коллекцию принудительно...")
                try:
                    embedding_service.qdrant_client.delete_collection("laliq_knowledge_base")
                    logger.info("✅ Коллекция удалена принудительно")
                except:
                    logger.info("ℹ️ Коллекция уже удалена или не существует")

        # Создаем новую коллекцию с правильным размером
        logger.info("🆕 Создаем новую коллекцию с размером векторов 1536...")
        await embedding_service.init_collection()

        # Проверяем результат
        try:
            new_collection_info = embedding_service.qdrant_client.get_collection("laliq_knowledge_base")
            try:
                new_vector_size = new_collection_info.config.params.vectors.size
                if new_vector_size == 1536:
                    logger.info("✅ Коллекция успешно создана с правильным размером векторов!")
                    logger.info("⚠️ Коллекция пуста, необходимо загрузить базу знаний:")
                    logger.info("   python load_knowledge_base.py")
                    return True
                else:
                    logger.error(f"❌ Ошибка: коллекция создана с неправильным размером {new_vector_size}")
                    return False
            except AttributeError:
                logger.info("✅ Коллекция создана (размер векторов не удалось проверить из-за API)")
                logger.info("⚠️ Коллекция пуста, необходимо загрузить базу знаний:")
                logger.info("   python load_knowledge_base.py")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке созданной коллекции: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при исправлении: {e}")
        return False


async def main():
    """Основная функция"""
    print("=" * 60)
    print("🔧 Исправление размерности векторов Qdrant")
    print("=" * 60)

    # Проверяем конфигурацию
    logger.info(f"🔧 Qdrant URL: {settings.qdrant_url}")
    logger.info(f"🔧 Qdrant API Key: {'*' * 20}...{settings.qdrant_api_key[-10:] if settings.qdrant_api_key else 'НЕ УСТАНОВЛЕН'}")

    # Исправляем размерность
    success = await fix_vector_dimensions()

    if success:
        print("\n" + "=" * 60)
        print("🎉 Исправление размерности векторов завершено!")
        print("📚 Теперь запустите: python load_knowledge_base.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Исправление не удалось!")
        print("🔍 Проверьте логи выше для деталей")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Операция прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
