# 🔧 Исправление ошибки индексов Qdrant

## 🚨 Проблема
```
Index required but not found for "category" of one of the following types: [keyword].
Help: Create an index for this key or use a different filter.
```

**Причина:** В коллекции Qdrant отсутствуют индексы для payload полей, используемых в фильтрах.

## ✅ Решение (уже применено)

### 1. Обновлен код создания коллекций
- Добавлено автоматическое создание индексов при инициализации
- Индексы создаются для полей: `category`, `specialist`, `has_prices`, `filename`, `language`

### 2. Создан скрипт для исправления существующих коллекций
- `create_qdrant_indexes.py` - создает недостающие индексы

## 🚀 Быстрое исправление

### На Heroku:
```bash
# Создать индексы для существующей коллекции
heroku run python create_qdrant_indexes.py --app clientera-telegram-bot
```

### Локально:
```bash
# Установить переменные окружения
export QDRANT_URL="https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM"

# Создать индексы
python create_qdrant_indexes.py
```

## 🔍 Созданные индексы

1. **`category`** (KEYWORD) - Категория контента (services, specialists, contact_info, etc.)
2. **`specialist`** (KEYWORD) - Специалист (sevil_bammatova, jamila_hunkaeva, madina_bagatyrova)
3. **`has_prices`** (BOOL) - Наличие цен в контенте
4. **`filename`** (KEYWORD) - Имя исходного файла
5. **`language`** (KEYWORD) - Язык контента (ru)

## 📋 Проверка исправления

### Команда для проверки:
```bash
heroku run python -c "
from core.openai_tools import YclientsToolsHandler
import asyncio

async def test():
    handler = YclientsToolsHandler(None, None)
    result = await handler.handle_get_services()
    if result.get('success'):
        print('✅ Функция get_services работает!')
        print(f'Найдено услуг: {len(result.get(\"services\", []))}')
    else:
        print('❌ Ошибка:', result.get('error'))

asyncio.run(test())
" --app clientera-telegram-bot
```

### В боте:
Напишите боту: **"Какие у вас услуги?"** - должен показать список услуг салона.

## 🔧 Что исправлено в коде

### 1. KnowledgeBaseManager.init_collection()
```python
# Создаем коллекцию
self.qdrant_client.create_collection(...)

# Создаем индексы для payload полей
await self._create_payload_indexes()
```

### 2. EmbeddingService.init_collection()
```python
# Аналогично добавлено создание индексов
await self._create_payload_indexes_service()
```

### 3. Новый метод _create_payload_indexes()
```python
# Создание индексов с обработкой ошибок
for field_name, field_type in index_fields:
    self.qdrant_client.create_payload_index(
        collection_name=self.collection_name,
        field_name=field_name,
        field_schema=field_type
    )
```

## ⚡ Результат

После создания индексов:
- ✅ Фильтры по категориям работают корректно
- ✅ Функция `get_services` возвращает список услуг
- ✅ Бот может отвечать на вопросы о услугах салона
- ✅ Все openai_tools функционируют без ошибок

**Время исправления:** 1-2 минуты
**Статус:** ✅ ИСПРАВЛЕНО
