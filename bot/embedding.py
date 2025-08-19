import os
import re
import markdown
import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
# Импорт OpenAIClient будет выполнен в методах для избежания циклических импортов
from config import settings
from database.database import SessionLocal

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    def __init__(self):
        # Подключение к Qdrant Cloud с поддержкой HTTPS
        if settings.qdrant_url.startswith("https://"):
            self.qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                https=True
            )
        else:
            self.qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
            )
        self.collection_name = "laliq_knowledge_base"
        self.knowledge_base_path = "./knowledge_base"

    async def init_collection(self):
        """Инициализация коллекции в Qdrant"""
        try:
            # Проверяем, существует ли коллекция
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name
                for collection in collections.collections
            )

            if not collection_exists:
                # Создаем коллекцию
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # Размер эмбеддингов text-embedding-3-small
                        distance=Distance.COSINE
                    )
                )
                print(f"Коллекция {self.collection_name} создана")
            else:
                print(f"Коллекция {self.collection_name} уже существует")

        except Exception as e:
            print(f"Ошибка при инициализации коллекции: {e}")

    def parse_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Парсинг Markdown файла на чанки по заголовкам ##"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Разделяем по заголовкам ##
            sections = re.split(r'\n## ', content)
            chunks = []

            for i, section in enumerate(sections):
                if not section.strip():
                    continue

                # Добавляем ## обратно (кроме первой секции)
                if i > 0:
                    section = "## " + section

                # Извлекаем заголовок
                lines = section.split('\n')
                title = lines[0].strip().replace('##', '').strip()

                # Получаем содержимое
                content_lines = lines[1:] if len(lines) > 1 else []
                content_text = '\n'.join(content_lines).strip()

                if content_text:
                    chunks.append({
                        "title": title,
                        "content": content_text,
                        "file_path": file_path,
                        "full_text": section
                    })

            return chunks

        except Exception as e:
            print(f"Ошибка при парсинге файла {file_path}: {e}")
            return []

    def get_all_markdown_files(self) -> List[str]:
        """Получение всех Markdown файлов из папки knowledge_base"""
        md_files = []

        if not os.path.exists(self.knowledge_base_path):
            os.makedirs(self.knowledge_base_path)
            print(f"Создана папка {self.knowledge_base_path}")
            return md_files

        for root, dirs, files in os.walk(self.knowledge_base_path):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))

        return md_files

    async def load_knowledge_base(self):
        """Загрузка всей базы знаний в Qdrant"""
        print("Начинаем загрузку базы знаний...")

        # Инициализируем коллекцию
        await self.init_collection()

        # Очищаем коллекцию
        self.qdrant_client.delete_collection(self.collection_name)
        await self.init_collection()

        # Получаем все файлы
        md_files = self.get_all_markdown_files()

        if not md_files:
            print("Markdown файлы не найдены в папке knowledge_base")
            return

        # Парсим все файлы
        all_chunks = []
        for file_path in md_files:
            chunks = self.parse_markdown_file(file_path)
            all_chunks.extend(chunks)

        if not all_chunks:
            print("Не найдено содержимого для загрузки")
            return

        print(f"Найдено {len(all_chunks)} чанков для загрузки")

        # Создаем эмбеддинги
        with SessionLocal() as db:
            from core.openai_client import OpenAIClient
            openai_client = OpenAIClient(db)

            # Подготавливаем тексты для эмбеддингов
            texts = [f"{chunk['title']}\n\n{chunk['content']}" for chunk in all_chunks]

            # Создаем эмбеддинги батчами
            batch_size = 100
            points = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_chunks = all_chunks[i:i + batch_size]

                embeddings = await openai_client.create_embeddings(batch_texts)

                for j, embedding in enumerate(embeddings):
                    chunk_idx = i + j
                    chunk = batch_chunks[j]

                    # Определяем категорию на основе файла и содержимого
                    category = self._determine_category(chunk["file_path"], chunk["content"])

                    # Определяем специалиста
                    specialist = self._determine_specialist(chunk["content"])

                    # Подсчитываем услуги и цены
                    service_info = self._analyze_services(chunk["content"])

                    point = PointStruct(
                        id=chunk_idx,
                        vector=embedding,
                        payload={
                            "title": chunk["title"],
                            "content": chunk["content"],
                            "file_path": chunk["file_path"],
                            "full_text": chunk["full_text"],
                            "category": category,
                            "specialist": specialist,
                            "service_count": service_info["count"],
                            "has_prices": service_info["has_prices"],
                            "price_range": service_info["price_range"] if service_info["has_prices"] else None,
                            "keywords": self._extract_keywords(chunk["content"]),
                            "content_length": len(chunk["content"]),
                            "language": "ru"
                        }
                    )
                    points.append(point)

                print(f"Обработано {min(i + batch_size, len(texts))} из {len(texts)} чанков")

            # Загружаем в Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            print(f"Загружено {len(points)} чанков в Qdrant")

    def _determine_category(self, file_path: str, content: str) -> str:
        """Определяем категорию на основе пути к файлу и содержимого"""
        file_path_lower = file_path.lower()
        content_lower = content.lower()

        # По имени файла
        if "staff_info" in file_path_lower or "specialists_info" in file_path_lower:
            return "specialists"
        elif "contact" in file_path_lower or "booking" in file_path_lower:
            return "contact_info"
        elif "pricing" in file_path_lower:
            return "pricing"
        elif "retail" in file_path_lower:
            return "retail"
        elif any(service in file_path_lower for service in ["services", "manicure", "hair", "cosmetology", "eyebrows", "eyelashes", "depilation", "injections", "other"]):
            return "services"

        # По содержимому
        if any(name in content for name in ["Севиль", "Джамиля", "Мадина", "Бамматова", "Хункаева", "Багатырова"]):
            return "specialists"
        elif "телефон" in content_lower and "запись" in content_lower:
            return "contact_info"
        elif "цена" in content_lower and "руб" in content_lower:
            if content_lower.count("₽") > 10:  # Много цен = прайс-лист
                return "pricing"
            else:
                return "services"
        elif "косметика" in content_lower and "продаж" in content_lower:
            return "retail"

        return "general"

    def _determine_specialist(self, content: str) -> str:
        """Определяем специалиста по содержимому"""
        if 'Севиль' in content or 'Бамматова' in content:
            return "sevil_bammatova"
        elif 'Джамиля' in content or 'Хункаева' in content:
            return "jamila_hunkaeva"
        elif 'Мадина' in content or 'Багатырова' in content:
            return "madina_bagatyrova"
        return None

    def _analyze_services(self, content: str) -> Dict[str, Any]:
        """Анализируем услуги и цены в контенте"""
        import re

        # Ищем цены
        price_patterns = [
            r'(\d+)\s*(?:₽|руб)',
            r'(\d+)\s*р\.',
            r'от\s*(\d+)\s*(?:₽|руб)'
        ]

        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            prices.extend([int(match) for match in matches])

        # Считаем услуги по заголовкам ###
        service_count = len(re.findall(r'^###\s+.+', content, re.MULTILINE))

        # Если нет заголовков, считаем по строкам с ценами
        if service_count == 0:
            service_count = len(set(prices))  # Уникальные цены

        has_prices = len(prices) > 0
        price_range = None

        if has_prices and prices:
            price_range = {
                "min": min(prices),
                "max": max(prices)
            }

        return {
            "count": service_count,
            "has_prices": has_prices,
            "price_range": price_range
        }

    def _extract_keywords(self, content: str) -> List[str]:
        """Извлекаем ключевые слова из контента"""
        import re

        # Основные ключевые слова для салона красоты
        beauty_keywords = [
            "маникюр", "педикюр", "брови", "ресницы", "волосы", "стрижка",
            "окрашивание", "массаж", "чистка", "пилинг", "депиляция",
            "ботокс", "филлер", "инъекции", "косметология", "spa"
        ]

        keywords = []
        content_lower = content.lower()

        for keyword in beauty_keywords:
            if keyword in content_lower:
                keywords.append(keyword)

        # Добавляем слова из заголовков
        headers = re.findall(r'###\s+(.+)', content)
        for header in headers:
            words = re.findall(r'\b[а-яё]{3,}\b', header.lower())
            keywords.extend(words[:3])  # Первые 3 слова

        return list(set(keywords))[:10]  # Максимум 10 уникальных ключевых слов

    async def search_knowledge_base(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск в базе знаний по запросу"""
        try:
            # Создаем эмбеддинг для запроса
            with SessionLocal() as db:
                from core.openai_client import OpenAIClient
                openai_client = OpenAIClient(db)
                query_embeddings = await openai_client.create_embeddings([query])

                if not query_embeddings:
                    return []

                query_embedding = query_embeddings[0]

            # Поиск в Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )

            results = []
            for result in search_results:
                results.append({
                    "title": result.payload["title"],
                    "content": result.payload["content"],
                    "file_path": result.payload["file_path"],
                    "score": result.score
                })

            return results

        except Exception as e:
            print(f"Ошибка при поиске в базе знаний: {e}")
            return []

    async def answer_question(self, question: str) -> str:
        """Ответ на вопрос с использованием базы знаний"""
        # Ищем релевантную информацию
        search_results = await self.search_knowledge_base(question, limit=3)

        if not search_results:
            return "Извините, я не нашел информации по вашему вопросу в базе знаний."

        # Формируем контекст
        context = "\n\n".join([
            f"**{result['title']}**\n{result['content']}"
            for result in search_results
        ])

        # Генерируем ответ с помощью GPT
        with SessionLocal() as db:
            from core.openai_client import OpenAIClient
            openai_client = OpenAIClient(db)

            messages = [
                {
                    "role": "system",
                    "content": """Ты - помощник в салоне красоты.
                    Отвечай на вопросы клиентов, используя только предоставленную информацию из базы знаний.
                    Если информации недостаточно, честно скажи об этом.
                    Отвечай дружелюбно и профессионально."""
                },
                {
                    "role": "user",
                    "content": f"""Вопрос клиента: {question}

                    Информация из базы знаний:
                    {context}

                    Ответь на вопрос, используя эту информацию."""
                }
            ]

            response = await openai_client.chat_completion(messages)
            return response

    def create_sample_knowledge_base(self):
        """Создание примера базы знаний"""
        if not os.path.exists(self.knowledge_base_path):
            os.makedirs(self.knowledge_base_path)

        sample_content = """# Информация о салоне красоты

## Услуги

### Маникюр
- Классический маникюр - 1500 руб., 60 мин
- Аппаратный маникюр - 1800 руб., 45 мин
- Покрытие гель-лаком - 800 руб., 30 мин

### Педикюр
- Классический педикюр - 2000 руб., 90 мин
- Аппаратный педикюр - 2200 руб., 75 мин

### Брови
- Коррекция бровей - 800 руб., 30 мин
- Окрашивание бровей - 600 руб., 20 мин
- Ламинирование бровей - 2500 руб., 60 мин

## Мастера

### Наталья Иванова
Специализация: маникюр, педикюр
Опыт работы: 5 лет
Работает: Пн-Пт 10:00-19:00

### Елена Петрова
Специализация: брови, ресницы
Опыт работы: 3 года
Работает: Вт-Сб 11:00-20:00

## Режим работы

Понедельник-Пятница: 10:00-20:00
Суббота: 10:00-18:00
Воскресенье: выходной

## Контакты

Адрес: г. Москва, ул. Примерная, д. 1
Телефон: +7 (495) 123-45-67
Email: info@salon.ru

## Правила записи

- Запись возможна за 14 дней вперед
- Отмена записи не позднее чем за 2 часа
- При опоздании более чем на 15 минут запись может быть отменена
"""

        sample_file = os.path.join(self.knowledge_base_path, "salon_info.md")
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)

        print(f"Создан пример базы знаний: {sample_file}")


# Функция для запуска загрузки базы знаний
async def main():
    kb_manager = KnowledgeBaseManager()

    # Создаем пример базы знаний если папка пуста
    if not kb_manager.get_all_markdown_files():
        kb_manager.create_sample_knowledge_base()

    # Загружаем базу знаний
    await kb_manager.load_knowledge_base()


class EmbeddingService:
    """Современный сервис для работы с эмбеддингами и Qdrant"""

    def __init__(self):
        # Подключение к Qdrant Cloud с поддержкой HTTPS
        if settings.qdrant_url.startswith("https://"):
            self.qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                https=True
            )
        else:
            self.qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
            )
        self.collection_name = "laliq_knowledge_base"

    async def init_collection(self):
        """Инициализация коллекции в Qdrant"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name
                for collection in collections.collections
            )

            if not collection_exists:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # Размер эмбеддингов text-embedding-3-small
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Коллекция {self.collection_name} создана")
            else:
                logger.info(f"Коллекция {self.collection_name} уже существует")

        except Exception as e:
            logger.error(f"Ошибка при инициализации коллекции: {e}")
            raise

    async def add_text(self, text: str, metadata: Dict[str, Any]) -> str:
        """Добавление текста в векторную базу"""
        try:
            # Создаем эмбеддинг
            with SessionLocal() as db:
                from core.openai_client import OpenAIClient
                openai_client = OpenAIClient(db)
                embeddings = await openai_client.create_embeddings([text])

                if not embeddings:
                    raise ValueError("Не удалось создать эмбеддинг")

                embedding = embeddings[0]

            # Генерируем уникальный ID
            point_id = str(uuid.uuid4())

            # Создаем точку для Qdrant
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=metadata
            )

            # Добавляем в Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            return point_id

        except Exception as e:
            logger.error(f"Ошибка при добавлении текста: {e}")
            raise

    async def search_similar(self, query: str, limit: int = 5, filter_conditions: Optional[Dict] = None):
        """Поиск похожих текстов"""
        try:
            # Автоматическая инициализация коллекции при первом обращении
            await self._ensure_collection_exists()

            # Создаем эмбеддинг для запроса
            with SessionLocal() as db:
                from core.openai_client import OpenAIClient
                openai_client = OpenAIClient(db)
                query_embeddings = await openai_client.create_embeddings([query])

                if not query_embeddings:
                    return []

                query_embedding = query_embeddings[0]

            # Подготавливаем фильтры
            search_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                search_filter = Filter(must=conditions)

            # Поиск в Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter
            )

            return search_results

        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return []

    async def _ensure_collection_exists(self):
        """Убеждаемся что коллекция существует"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name
                for collection in collections.collections
            )

            if not collection_exists:
                logger.info(f"Коллекция {self.collection_name} не найдена, создаем...")
                await self.init_collection()
                logger.info(f"Коллекция {self.collection_name} создана (пустая)")
                logger.warning("База знаний пуста! Необходимо загрузить данные с помощью скрипта загрузки.")

        except Exception as e:
            logger.error(f"Ошибка проверки коллекции: {e}")
            # Попытаемся создать коллекцию в любом случае
            try:
                await self.init_collection()
                logger.info("Коллекция создана принудительно")
            except Exception as init_error:
                logger.error(f"Не удалось создать коллекцию: {init_error}")
                raise

    async def delete_points(self, point_ids: List[str]):
        """Удаление точек по ID"""
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            logger.info(f"Удалено {len(point_ids)} точек")
        except Exception as e:
            logger.error(f"Ошибка при удалении точек: {e}")
            raise

    async def clear_collection(self):
        """Очистка всей коллекции"""
        try:
            # Получаем все точки
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000
            )

            if scroll_result[0]:  # Если есть точки
                point_ids = [point.id for point in scroll_result[0]]
                await self.delete_points(point_ids)
                logger.info(f"Коллекция {self.collection_name} очищена")
            else:
                logger.info(f"Коллекция {self.collection_name} уже пуста")

        except Exception as e:
            logger.error(f"Ошибка при очистке коллекции: {e}")
            raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
