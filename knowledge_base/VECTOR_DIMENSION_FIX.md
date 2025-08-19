# ⚡ Исправление ошибки размерности векторов

## 🚨 Проблема
```
Vector dimension error: expected dim: 3072, got 1536
```

**Причина:** Коллекция в Qdrant была создана для векторов размером 3072 (text-embedding-3-large), но код использует text-embedding-3-small (размер 1536).

## ✅ Решение (уже применено)

### 1. Обновлен код в `bot/embedding.py`
- Изменен размер коллекции с 3072 на 1536
- Соответствует используемой модели `text-embedding-3-small`

### 2. Обновлен скрипт миграции
- `migrate_to_qdrant_cloud.py`: VECTOR_SIZE = 1536

### 3. Необходимо пересоздать коллекцию

## 🚀 Команды для исправления

### На Heroku:
```bash
# 1. Удалить старую коллекцию и создать новую с правильным размером
heroku run python -c "
from bot.embedding import EmbeddingService
import asyncio

async def fix_collection():
    service = EmbeddingService()
    try:
        # Удаляем старую коллекцию
        service.qdrant_client.delete_collection('laliq_knowledge_base')
        print('Старая коллекция удалена')
    except:
        print('Коллекция уже удалена или не существует')

    # Создаем новую с правильным размером
    await service.init_collection()
    print('Новая коллекция создана с размером векторов 1536')

asyncio.run(fix_collection())
" --app clientera-telegram-bot

# 2. Загрузить базу знаний
heroku run python load_knowledge_base.py --app clientera-telegram-bot
```

### Локально (если есть доступ):
```bash
export QDRANT_URL="https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM"

python -c "
from bot.embedding import EmbeddingService
import asyncio

async def fix_collection():
    service = EmbeddingService()
    try:
        service.qdrant_client.delete_collection('laliq_knowledge_base')
        print('Старая коллекция удалена')
    except:
        print('Коллекция уже удалена или не существует')

    await service.init_collection()
    print('Новая коллекция создана')

asyncio.run(fix_collection())
"

python load_knowledge_base.py
```

## 🔍 Проверка исправления

```bash
heroku run python -c "
from bot.embedding import EmbeddingService
import asyncio

async def test():
    service = EmbeddingService()
    results = await service.search_similar('маникюр', limit=1)
    print(f'✅ Поиск работает! Найдено: {len(results)} результатов')
    if results:
        print(f'Релевантность: {results[0].score:.3f}')

asyncio.run(test())
" --app clientera-telegram-bot
```

## 📋 Что было исправлено

- ✅ Размер векторов в коде: 3072 → 1536
- ✅ Соответствие модели: text-embedding-3-small
- ✅ Обновлена документация
- ✅ Обновлен скрипт миграции

**Время исправления:** 1-2 минуты
**Статус:** Готово к применению
