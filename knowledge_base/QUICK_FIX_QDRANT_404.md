# ⚡ Быстрое исправление ошибки Qdrant 404

## 🚨 Проблема
```
ERROR - Ошибка при поиске: Unexpected Response: 404 (Not Found)
Collection `laliq_knowledge_base` doesn't exist!
```

## ⚡ Быстрое решение

### Вариант 1: Автоматическое исправление (уже реализовано)
Код уже обновлен - коллекция будет создаваться автоматически при первом обращении к поиску.

### Вариант 2: Загрузка базы знаний на Heroku
```bash
# Загрузить базу знаний
heroku run python load_knowledge_base.py --app clientera-telegram-bot

# Проверить результат
heroku run python -c "
import asyncio
from bot.embedding import EmbeddingService
service = EmbeddingService()
results = asyncio.run(service.search_similar('маникюр', limit=1))
print(f'Поиск работает! Найдено: {len(results)} результатов')
" --app clientera-telegram-bot
```

### Вариант 3: Локальная загрузка (если есть доступ к переменным окружения)
```bash
# Установить переменные окружения
export QDRANT_URL="https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM"

# Запустить загрузку
python load_knowledge_base.py
```

## ✅ Проверка исправления

После любого из вариантов ошибка должна исчезнуть, и бот будет отвечать на вопросы используя базу знаний.

**Время исправления:** 2-5 минут
**Статус:** Готово к применению
