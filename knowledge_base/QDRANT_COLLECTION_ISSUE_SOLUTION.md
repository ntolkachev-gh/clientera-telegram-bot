# 🔧 Решение проблемы с отсутствующей коллекцией Qdrant

## 🚨 Описание проблемы

При работе бота на Heroku возникает ошибка:
```
2025-08-19 18:32:32,259 - bot.embedding - ERROR - Ошибка при поиске: Unexpected Response: 404 (Not Found)
Raw response content:
b'{"status":{"error":"Not found: Collection `laliq_knowledge_base` doesn\'t exist!"},"time":3.162e-6}'
```

**Причина:** Коллекция `laliq_knowledge_base` не была создана в Qdrant Cloud после деплоя на Heroku.

## 🔍 Анализ проблемы

### Текущая конфигурация Qdrant Cloud:
- **URL:** `https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io`
- **API Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM`
- **Коллекция:** `laliq_knowledge_base`
- **Размер векторов:** 1536 (text-embedding-3-small)

### Проблема в коде:
1. `EmbeddingService.search_similar()` в `bot/embedding.py` пытается выполнить поиск в несуществующей коллекции
2. Метод `init_collection()` вызывается только при загрузке базы знаний, но не при поиске
3. На Heroku коллекция не была инициализирована после деплоя

## 🛠️ Решения

### 1. Быстрое решение - Инициализация коллекции при запуске бота

Добавить автоматическую инициализацию коллекции в `EmbeddingService.search_similar()`:

```python
async def search_similar(self, query: str, limit: int = 5, filter_conditions: Optional[Dict] = None):
    """Поиск похожих текстов"""
    try:
        # Проверяем и создаем коллекцию если нужно
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name
                for collection in collections.collections
            )
            if not collection_exists:
                await self.init_collection()
        except Exception as init_error:
            logger.warning(f"Ошибка проверки коллекции: {init_error}")
            await self.init_collection()

        # Остальной код поиска...
```

### 2. Полное решение - Запуск миграции данных

#### Опция А: Использование существующего скрипта миграции

```bash
# На локальной машине
python migrate_to_qdrant_cloud.py
```

Выбрать опцию 2 (загрузка из файлов knowledge base)

#### Опция Б: Использование скрипта загрузки из optimized_chunks

```bash
# Установить переменные окружения
export QDRANT_URL="https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM"

# Запустить загрузку
cd knowledge_base/optimized_chunks
python load_to_qdrant.py
```

#### Опция В: Использование KnowledgeBaseManager

```python
# В Python консоли или отдельном скрипте
import asyncio
from bot.embedding import KnowledgeBaseManager

async def setup_knowledge_base():
    kb_manager = KnowledgeBaseManager()
    await kb_manager.load_knowledge_base()

# Запуск
asyncio.run(setup_knowledge_base())
```

### 3. Рекомендуемое решение для продакшена

#### Шаг 1: Обновить код для автоматической инициализации

Модифицировать `bot/embedding.py` - добавить проверку коллекции в `search_similar()`:

```python
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
            logger.info(f"Коллекция {self.collection_name} создана")

    except Exception as e:
        logger.error(f"Ошибка проверки коллекции: {e}")
        raise
```

#### Шаг 2: Добавить команду для загрузки базы знаний

Создать отдельный скрипт для загрузки данных на Heroku:

```python
# load_knowledge_base.py
import asyncio
import os
from bot.embedding import KnowledgeBaseManager

async def main():
    """Загрузка базы знаний в Qdrant Cloud"""
    print("🚀 Начинаем загрузку базы знаний в Qdrant Cloud...")

    kb_manager = KnowledgeBaseManager()
    await kb_manager.load_knowledge_base()

    print("✅ База знаний успешно загружена!")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Шаг 3: Обновить деплой процесс

Добавить в `deploy_to_heroku.sh` команду для загрузки базы знаний:

```bash
# После деплоя приложения
echo "📚 Загружаем базу знаний..."
heroku run python load_knowledge_base.py --app laliq-beauty-bot
```

## 🔍 Проверка решения

### 1. Проверка подключения к Qdrant Cloud

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM",
    https=True
)

# Проверяем коллекции
collections = client.get_collections()
print(f"Найдено коллекций: {len(collections.collections)}")

# Проверяем конкретную коллекцию
try:
    info = client.get_collection("laliq_knowledge_base")
    print(f"Коллекция laliq_knowledge_base: {info.points_count} точек")
except Exception as e:
    print(f"Коллекция не найдена: {e}")
```

### 2. Тестирование поиска

```python
import asyncio
from bot.embedding import EmbeddingService

async def test_search():
    service = EmbeddingService()
    results = await service.search_similar("маникюр цены", limit=3)
    print(f"Найдено результатов: {len(results)}")
    for result in results:
        print(f"- {result.payload.get('title', 'Без названия')}: {result.score:.3f}")

asyncio.run(test_search())
```

## 📋 Чек-лист для исправления

- [ ] Обновить код `EmbeddingService.search_similar()` с автоматической инициализацией
- [ ] Создать скрипт `load_knowledge_base.py` для загрузки данных
- [ ] Запустить загрузку базы знаний локально или на Heroku
- [ ] Проверить работу поиска в боте
- [ ] Обновить процесс деплоя для автоматической загрузки данных

## 🚨 Критические моменты

1. **Размер векторов:** Убедиться что используется правильный размер (1536 для text-embedding-3-small)
2. **API ключи:** Проверить актуальность API ключа Qdrant Cloud
3. **Переменные окружения:** Убедиться что на Heroku установлены правильные значения `QDRANT_URL` и `QDRANT_API_KEY`
4. **Совместимость моделей:** Если меняли модель эмбеддингов, нужно пересоздать коллекцию

## 🔄 План восстановления

1. **Немедленно:** Добавить автоматическую инициализацию коллекции в код
2. **В течение часа:** Загрузить базу знаний в Qdrant Cloud
3. **Долгосрочно:** Автоматизировать процесс загрузки данных при деплое

---

**Дата создания:** 2025-08-19
**Статус:** Готово к применению
**Приоритет:** Критический
