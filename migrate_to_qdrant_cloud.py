#!/usr/bin/env python3
"""
Скрипт для миграции данных из локального Qdrant в Qdrant Cloud
"""

import os
import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация Qdrant Cloud
QDRANT_CLOUD_URL = "https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_CLOUD_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM"

# Конфигурация локального Qdrant (для миграции)
LOCAL_QDRANT_URL = "http://localhost:6333"

COLLECTION_NAME = "laliq_knowledge_base"
VECTOR_SIZE = 1536  # Размер вектора для text-embedding-3-small


def create_cloud_collection(client: QdrantClient):
    """Создание коллекции в Qdrant Cloud"""
    try:
        # Проверяем существование коллекции
        collections = client.get_collections()
        if COLLECTION_NAME in [c.name for c in collections.collections]:
            logger.info(f"Коллекция {COLLECTION_NAME} уже существует в Qdrant Cloud")
            # Опционально: удалить существующую коллекцию
            response = input("Удалить существующую коллекцию и создать заново? (y/n): ")
            if response.lower() == 'y':
                client.delete_collection(COLLECTION_NAME)
                logger.info(f"Коллекция {COLLECTION_NAME} удалена")
            else:
                return

        # Создаем новую коллекцию
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        logger.info(f"Коллекция {COLLECTION_NAME} создана в Qdrant Cloud")
    except Exception as e:
        logger.error(f"Ошибка при создании коллекции: {e}")
        raise


def migrate_from_local():
    """Миграция данных из локального Qdrant в Cloud"""
    try:
        # Подключение к локальному Qdrant
        logger.info("Подключение к локальному Qdrant...")
        local_client = QdrantClient(url=LOCAL_QDRANT_URL)

        # Подключение к Qdrant Cloud
        logger.info("Подключение к Qdrant Cloud...")
        cloud_client = QdrantClient(
            url=QDRANT_CLOUD_URL,
            api_key=QDRANT_CLOUD_API_KEY,
            https=True
        )

        # Проверка локальной коллекции
        local_collections = local_client.get_collections()
        if COLLECTION_NAME not in [c.name for c in local_collections.collections]:
            logger.error(f"Коллекция {COLLECTION_NAME} не найдена в локальном Qdrant")
            return False

        # Создание коллекции в Cloud
        create_cloud_collection(cloud_client)

        # Получение всех точек из локальной коллекции
        logger.info("Получение данных из локальной коллекции...")
        offset = None
        total_migrated = 0
        batch_size = 100

        while True:
            # Получаем batch точек
            response = local_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            points = response[0]
            if not points:
                break

            # Загружаем точки в Cloud
            logger.info(f"Загрузка {len(points)} точек в Qdrant Cloud...")
            cloud_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )

            total_migrated += len(points)
            logger.info(f"Загружено {total_migrated} точек")

            # Обновляем offset для следующего batch
            offset = response[1]
            if offset is None:
                break

        logger.info(f"Миграция завершена! Всего перенесено {total_migrated} точек")

        # Проверка результата
        cloud_collection_info = cloud_client.get_collection(COLLECTION_NAME)
        logger.info(f"Количество точек в Cloud: {cloud_collection_info.points_count}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при миграции: {e}")
        return False


def migrate_from_files():
    """Альтернативный метод: загрузка данных из файлов knowledge base напрямую в Cloud"""
    try:
        logger.info("Загрузка данных из файлов knowledge base...")

        # Подключение к Qdrant Cloud
        cloud_client = QdrantClient(
            url=QDRANT_CLOUD_URL,
            api_key=QDRANT_CLOUD_API_KEY,
            https=True
        )

        # Создание коллекции
        create_cloud_collection(cloud_client)

        # Проверяем наличие скрипта загрузки
        load_script_path = "knowledge_base/optimized_chunks/load_to_qdrant.py"
        if os.path.exists(load_script_path):
            logger.info("Используем существующий скрипт загрузки...")
            # Временно обновляем переменные окружения для скрипта
            os.environ['QDRANT_URL'] = QDRANT_CLOUD_URL
            os.environ['QDRANT_API_KEY'] = QDRANT_CLOUD_API_KEY

            # Запускаем скрипт загрузки
            import subprocess
            result = subprocess.run([sys.executable, load_script_path], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Данные успешно загружены в Qdrant Cloud")
                logger.info(result.stdout)
            else:
                logger.error(f"Ошибка при загрузке: {result.stderr}")
                return False
        else:
            logger.error(f"Скрипт загрузки не найден: {load_script_path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Ошибка при загрузке из файлов: {e}")
        return False


def test_cloud_connection():
    """Тестирование подключения к Qdrant Cloud"""
    try:
        logger.info("Тестирование подключения к Qdrant Cloud...")
        client = QdrantClient(
            url=QDRANT_CLOUD_URL,
            api_key=QDRANT_CLOUD_API_KEY,
            https=True
        )

        # Получаем информацию о коллекциях
        collections = client.get_collections()
        logger.info(f"Подключение успешно! Найдено коллекций: {len(collections.collections)}")

        for collection in collections.collections:
            info = client.get_collection(collection.name)
            logger.info(f"  - {collection.name}: {info.points_count} точек")

        return True

    except Exception as e:
        logger.error(f"Ошибка подключения к Qdrant Cloud: {e}")
        return False


def main():
    """Основная функция"""
    print("=" * 60)
    print("Миграция данных на Qdrant Cloud")
    print("=" * 60)

    # Тестируем подключение к Cloud
    if not test_cloud_connection():
        logger.error("Не удалось подключиться к Qdrant Cloud")
        return

    print("\nВыберите метод миграции:")
    print("1. Миграция из локального Qdrant (если он запущен)")
    print("2. Загрузка из файлов knowledge base")
    print("3. Только тестирование подключения")

    choice = input("\nВаш выбор (1/2/3): ").strip()

    if choice == "1":
        # Проверяем доступность локального Qdrant
        try:
            local_client = QdrantClient(url=LOCAL_QDRANT_URL)
            local_client.get_collections()
            logger.info("Локальный Qdrant доступен, начинаем миграцию...")
            if migrate_from_local():
                logger.info("✅ Миграция успешно завершена!")
            else:
                logger.error("❌ Миграция не удалась")
        except Exception as e:
            logger.error(f"Локальный Qdrant недоступен: {e}")
            logger.info("Попробуйте запустить Docker с Qdrant или выберите вариант 2")

    elif choice == "2":
        if migrate_from_files():
            logger.info("✅ Загрузка данных успешно завершена!")
        else:
            logger.error("❌ Загрузка не удалась")

    elif choice == "3":
        logger.info("Тестирование завершено")
    else:
        logger.error("Неверный выбор")


if __name__ == "__main__":
    main()
