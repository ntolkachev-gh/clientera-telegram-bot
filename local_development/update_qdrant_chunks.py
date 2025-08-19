#!/usr/bin/env python3
"""
Обновление чанков в Qdrant с новой структурой базы знаний
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.embedding import EmbeddingService
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QdrantUpdater:
    """Обновление векторной базы данных Qdrant"""

    def __init__(self):
        self.kb_dir = Path("knowledge_base")
        self.embedding_service = EmbeddingService()

        # Загружаем маппинг чанков
        self.chunks_mapping = self.load_chunks_mapping()

    def load_chunks_mapping(self) -> Dict[str, Any]:
        """Загрузка маппинга чанков"""
        mapping_file = self.kb_dir / "chunks_mapping.json"

        if not mapping_file.exists():
            raise FileNotFoundError(f"Файл маппинга не найден: {mapping_file}")

        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_md_files_by_priority(self) -> List[tuple]:
        """Получение MD файлов отсортированных по приоритету"""
        files_info = []

        for filename, file_info in self.chunks_mapping['files'].items():
            if filename.endswith('.md') and filename != 'chunks_info.md':
                file_path = self.kb_dir / filename
                if file_path.exists():
                    files_info.append((
                        filename,
                        file_path,
                        file_info['priority'],
                        file_info['chunk_type']
                    ))

        # Сортируем по приоритету (1 = высший)
        files_info.sort(key=lambda x: x[2])
        return files_info

    def create_chunk_metadata(self, filename: str, chunk_type: str, priority: int, content: str) -> Dict[str, Any]:
        """Создание метаданных для чанка"""
        return {
            "filename": filename,
            "chunk_type": chunk_type,
            "priority": priority,
            "content_length": len(content),
            "source": "yclients_api",
            "created_at": self.chunks_mapping['created_at'],
            "category": self.get_category_for_file(filename),
            "is_service_info": chunk_type == "services_category",
            "is_general_info": chunk_type in ["general_info", "booking"],
            "is_pricing": chunk_type == "pricing",
            "is_staff": chunk_type == "staff"
        }

    def get_category_for_file(self, filename: str) -> str:
        """Получение категории для файла"""
        # Ищем в категориях из маппинга
        for cat_key, cat_data in self.chunks_mapping.get('categories', {}).items():
            if cat_data.get('filename') == filename:
                return cat_data['name']

        # Возвращаем тип чанка как категорию
        file_info = self.chunks_mapping['files'].get(filename, {})
        chunk_type = file_info.get('chunk_type', 'other')

        type_to_category = {
            'general_info': 'Общая информация',
            'booking': 'Запись и контакты',
            'pricing': 'Цены и услуги',
            'staff': 'Специалисты',
            'services_category': 'Категория услуг',
            'other': 'Прочее'
        }

        return type_to_category.get(chunk_type, 'Прочее')

    async def clear_existing_chunks(self):
        """Очистка существующих чанков в Qdrant"""
        print("🗑️  ОЧИСТКА СУЩЕСТВУЮЩИХ ЧАНКОВ")
        print("=" * 50)

        try:
            # Получаем все точки из коллекции
            existing_points = await self.embedding_service.search_similar("test", limit=1000)

            if existing_points:
                print(f"📊 Найдено существующих чанков: {len(existing_points)}")

                # Удаляем все существующие точки
                point_ids = [point.id for point in existing_points]
                await self.embedding_service.delete_points(point_ids)

                print(f"❌ Удалено {len(point_ids)} старых чанков")
            else:
                print("📭 Существующих чанков не найдено")

            print("✅ Очистка завершена")
            print()

        except Exception as e:
            print(f"⚠️ Ошибка при очистке (возможно, коллекция пустая): {str(e)}")
            print("▶️ Продолжаем загрузку новых чанков...")
            print()

    async def upload_chunks_to_qdrant(self):
        """Загрузка новых чанков в Qdrant"""
        print("📤 ЗАГРУЗКА НОВЫХ ЧАНКОВ В QDRANT")
        print("=" * 50)

        files_info = self.get_md_files_by_priority()

        if not files_info:
            print("❌ Не найдено MD файлов для загрузки")
            return False

        successful_uploads = 0

        for filename, file_path, priority, chunk_type in files_info:
            try:
                print(f"📄 Обрабатываем: {filename} (приоритет: {priority})")

                # Читаем содержимое файла
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Создаем метаданные
                metadata = self.create_chunk_metadata(filename, chunk_type, priority, content)

                # Добавляем в Qdrant
                point_id = await self.embedding_service.add_text(
                    text=content,
                    metadata=metadata
                )

                print(f"✅ Загружен чанк: {filename} (ID: {point_id})")
                print(f"   📊 Размер: {len(content)} символов")
                print(f"   🏷️ Категория: {metadata['category']}")
                print()

                successful_uploads += 1

            except Exception as e:
                print(f"❌ Ошибка при загрузке {filename}: {str(e)}")
                logger.exception(f"Детали ошибки для {filename}:")
                print()

        print(f"📊 РЕЗУЛЬТАТ: {successful_uploads}/{len(files_info)} чанков загружено успешно")
        return successful_uploads > 0

    async def verify_upload(self):
        """Проверка загруженных чанков"""
        print("🔍 ПРОВЕРКА ЗАГРУЖЕННЫХ ЧАНКОВ")
        print("=" * 50)

        try:
            # Выполняем тестовый поиск
            test_queries = [
                "информация о салоне",
                "маникюр цена",
                "запись на услуги",
                "специалисты мастера",
                "депиляция ноги"
            ]

            for query in test_queries:
                print(f"🔎 Тестовый запрос: '{query}'")

                results = await self.embedding_service.search_similar(query, limit=3)

                if results:
                    print(f"   ✅ Найдено {len(results)} результатов:")
                    for i, result in enumerate(results, 1):
                        metadata = result.payload
                        filename = metadata.get('filename', 'unknown')
                        category = metadata.get('category', 'unknown')
                        score = result.score
                        print(f"      {i}. {filename} ({category}) - score: {score:.3f}")
                else:
                    print("   ❌ Результатов не найдено")
                print()

            # Проверяем общее количество чанков
            all_results = await self.embedding_service.search_similar("test", limit=100)
            print(f"📊 Всего чанков в базе: {len(all_results)}")

            # Группируем по типам
            chunk_types = {}
            for result in all_results:
                chunk_type = result.payload.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

            print("📈 Распределение по типам:")
            for chunk_type, count in chunk_types.items():
                print(f"   - {chunk_type}: {count} чанков")

            print("✅ Проверка завершена")
            return True

        except Exception as e:
            print(f"❌ Ошибка при проверке: {str(e)}")
            logger.exception("Детали ошибки:")
            return False

    async def update_qdrant_complete(self):
        """Полное обновление Qdrant"""
        print("🚀 ПОЛНОЕ ОБНОВЛЕНИЕ QDRANT")
        print("=" * 70)
        print(f"📁 Директория базы знаний: {self.kb_dir.absolute()}")
        print(f"📊 Файлов к обработке: {len([f for f in self.chunks_mapping['files'] if f.endswith('.md') and f != 'chunks_info.md'])}")
        print()

        try:
            # 1. Очистка существующих чанков
            await self.clear_existing_chunks()

            # 2. Загрузка новых чанков
            success = await self.upload_chunks_to_qdrant()

            if not success:
                print("❌ Загрузка чанков не удалась")
                return False

            # 3. Проверка результата
            verification_success = await self.verify_upload()

            if verification_success:
                print("\n🎉 ОБНОВЛЕНИЕ QDRANT ЗАВЕРШЕНО УСПЕШНО!")
                print("=" * 70)
                print("✅ Все чанки загружены и проверены")
                print("🔍 Поиск работает корректно")
                print("📊 База знаний готова к использованию")
                return True
            else:
                print("\n⚠️ ОБНОВЛЕНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
                print("=" * 70)
                print("✅ Чанки загружены")
                print("⚠️ Проверка выявила проблемы")
                return True

        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ОБНОВЛЕНИИ: {str(e)}")
            logger.exception("Детали критической ошибки:")
            return False


async def main():
    """Основная функция"""
    try:
        updater = QdrantUpdater()
        success = await updater.update_qdrant_complete()

        if success:
            print("\n📝 Обновление завершено!")
            print("🤖 Бот готов к работе с новой базой знаний")
            return 0
        else:
            print("\n❌ Обновление завершилось с ошибками")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        logger.exception("Детали:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
