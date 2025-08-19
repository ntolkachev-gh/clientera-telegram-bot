#!/usr/bin/env python3
"""
Скрипт для загрузки оптимизированных чанков базы знаний в Qdrant
Автор: AI Assistant
Дата: 2025
"""

import os
import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import requests
from sentence_transformers import SentenceTransformer
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QdrantLoader:
    """Класс для загрузки чанков в Qdrant"""

    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "laliq_knowledge_base"):
        self.qdrant_url = qdrant_url.rstrip('/')
        self.collection_name = collection_name
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.vector_size = 384  # Размер векторов для выбранной модели

    def create_collection(self) -> bool:
        """Создает коллекцию в Qdrant"""
        collection_config = {
            "vectors": {
                "size": self.vector_size,
                "distance": "Cosine"
            },
            "optimizers_config": {
                "default_segment_number": 2
            },
            "replication_factor": 1
        }

        try:
            # Проверяем, существует ли коллекция
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                logger.info(f"Коллекция '{self.collection_name}' уже существует")
                return True

            # Создаем коллекцию
            response = requests.put(
                f"{self.qdrant_url}/collections/{self.collection_name}",
                json=collection_config,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 201]:
                logger.info(f"Коллекция '{self.collection_name}' успешно создана")
                return True
            else:
                logger.error(f"Ошибка создания коллекции: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при работе с коллекцией: {e}")
            return False

    def generate_chunk_id(self, filename: str, content: str) -> str:
        """Генерирует уникальный UUID для чанка"""
        # Создаем детерминированный UUID на основе имени файла и содержимого
        seed = f"{filename}_{hashlib.md5(content.encode('utf-8')).hexdigest()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))

    def extract_metadata_from_content(self, content: str, filename: str) -> Dict[str, Any]:
        """Извлекает метаданные из содержимого файла"""
        lines = content.split('\n')
        title = ""
        category = ""
        service_count = 0
        price_range = {"min": None, "max": None}
        keywords = []

        # Извлекаем заголовок
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # Определяем категорию по имени файла
        if 'contact' in filename:
            category = "contact_info"
        elif 'specialist' in filename:
            category = "specialists"
        elif 'services_' in filename:
            category = "services"
        elif 'pricing' in filename:
            category = "pricing"
        elif 'retail' in filename:
            category = "retail"
        else:
            category = "general"

        # Подсчитываем услуги и извлекаем цены
        for line in lines:
            if '**Цена:**' in line:
                service_count += 1
                # Извлекаем цену
                try:
                    price_text = line.split('**Цена:**')[1].strip()
                    price = int(''.join(filter(str.isdigit, price_text.split()[0])))
                    if price_range["min"] is None or price < price_range["min"]:
                        price_range["min"] = price
                    if price_range["max"] is None or price > price_range["max"]:
                        price_range["max"] = price
                except:
                    pass

        # Извлекаем ключевые слова из заголовков
        for line in lines:
            if line.startswith('###') or line.startswith('##'):
                words = line.replace('#', '').strip().lower()
                keywords.extend([w.strip() for w in words.split() if len(w.strip()) > 2])

        # Определяем специалиста по содержимому
        specialist = None
        if 'Севиль' in content or 'Бамматова' in content:
            specialist = "sevil_bammatova"
        elif 'Джамиля' in content or 'Хункаева' in content:
            specialist = "jamila_hunkaeva"
        elif 'Мадина' in content or 'Багатырова' in content:
            specialist = "madina_bagatyrova"

        return {
            "title": title,
            "category": category,
            "filename": filename,
            "service_count": service_count,
            "price_range": price_range if price_range["min"] is not None else None,
            "specialist": specialist,
            "keywords": list(set(keywords))[:10],  # Ограничиваем до 10 уникальных ключевых слов
            "content_length": len(content),
            "has_prices": service_count > 0,
            "language": "ru"
        }

    def load_chunk(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Загружает один чанк из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                logger.warning(f"Файл {filepath.name} пустой, пропускаем")
                return None

            # Генерируем вектор
            vector = self.model.encode(content).tolist()

            # Извлекаем метаданные
            metadata = self.extract_metadata_from_content(content, filepath.name)

            # Создаем ID
            chunk_id = self.generate_chunk_id(filepath.name, content)

            return {
                "id": chunk_id,
                "vector": vector,
                "payload": {
                    "content": content,
                    **metadata
                }
            }

        except Exception as e:
            logger.error(f"Ошибка при обработке файла {filepath}: {e}")
            return None

    def upload_chunks(self, chunks_dir: Path) -> bool:
        """Загружает все чанки в Qdrant"""
        try:
            # Получаем все .md файлы
            md_files = list(chunks_dir.glob("*.md"))
            if not md_files:
                logger.error("Не найдено .md файлов для загрузки")
                return False

            logger.info(f"Найдено {len(md_files)} файлов для загрузки")

            points = []
            for filepath in md_files:
                logger.info(f"Обрабатываем файл: {filepath.name}")
                chunk = self.load_chunk(filepath)
                if chunk:
                    points.append(chunk)
                    logger.info(f"✓ {filepath.name} - {len(chunk['payload']['content'])} символов")

            if not points:
                logger.error("Не удалось загрузить ни одного чанка")
                return False

            # Отправляем в Qdrant
            upload_data = {
                "points": points
            }

            response = requests.put(
                f"{self.qdrant_url}/collections/{self.collection_name}/points",
                json=upload_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 201]:
                logger.info(f"✅ Успешно загружено {len(points)} чанков в Qdrant")
                return True
            else:
                logger.error(f"❌ Ошибка загрузки: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при загрузке чанков: {e}")
            return False

    def test_search(self, query: str = "запись к мастеру", limit: int = 3) -> bool:
        """Тестирует поиск в загруженной коллекции"""
        try:
            # Генерируем вектор для запроса
            query_vector = self.model.encode(query).tolist()

            search_data = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True
            }

            response = requests.post(
                f"{self.qdrant_url}/collections/{self.collection_name}/points/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"🔍 Тестовый поиск по запросу '{query}':")
                for i, result in enumerate(results.get('result', []), 1):
                    title = result['payload'].get('title', 'Без названия')
                    score = result['score']
                    logger.info(f"  {i}. {title} (релевантность: {score:.3f})")
                return True
            else:
                logger.error(f"Ошибка поиска: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при тестировании поиска: {e}")
            return False

    def get_collection_info(self) -> bool:
        """Получает информацию о коллекции"""
        try:
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                info = response.json()
                points_count = info['result']['points_count']
                vectors_count = info['result']['vectors_count']
                logger.info(f"📊 Информация о коллекции '{self.collection_name}':")
                logger.info(f"  - Точек: {points_count}")
                logger.info(f"  - Векторов: {vectors_count}")
                return True
            else:
                logger.error(f"Ошибка получения информации: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при получении информации о коллекции: {e}")
            return False

def main():
    """Основная функция"""
    logger.info("🚀 Запуск загрузки базы знаний в Qdrant")

    # Путь к папке с чанками
    chunks_dir = Path(__file__).parent

    # Создаем загрузчик
    loader = QdrantLoader()

    # Проверяем подключение к Qdrant
    try:
        response = requests.get(f"{loader.qdrant_url}/collections")
        if response.status_code != 200:
            logger.error(f"❌ Не удается подключиться к Qdrant по адресу {loader.qdrant_url}")
            logger.error("Убедитесь, что Qdrant запущен и доступен")
            return
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Qdrant: {e}")
        return

    logger.info("✅ Подключение к Qdrant установлено")

    # Создаем коллекцию
    if not loader.create_collection():
        return

    # Загружаем чанки
    if not loader.upload_chunks(chunks_dir):
        return

    # Получаем информацию о коллекции
    loader.get_collection_info()

    # Тестируем поиск
    test_queries = [
        "запись к мастеру",
        "цены на маникюр",
        "наращивание ресниц",
        "специалисты салона"
    ]

    logger.info("🧪 Тестирование поиска:")
    for query in test_queries:
        loader.test_search(query, limit=2)

    logger.info("🎉 Загрузка завершена успешно!")
    logger.info(f"💡 Коллекция '{loader.collection_name}' готова к использованию")

if __name__ == "__main__":
    main()
