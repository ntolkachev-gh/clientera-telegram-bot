# Clientera Telegram Bot - Production

## 🚀 Быстрый старт

### 1. Миграция данных в Qdrant Cloud

```bash
# Запустите скрипт миграции
python migrate_to_qdrant_cloud.py

# Выберите опцию:
# 1 - Если у вас запущен локальный Qdrant с данными
# 2 - Для загрузки из файлов knowledge_base
```

### 2. Деплой на Heroku

```bash
# Автоматический деплой
./deploy_to_heroku.sh
```

Или вручную:

```bash
# Создание приложения
heroku create clientera-telegram-bot

# Добавление PostgreSQL
heroku addons:create heroku-postgresql:mini

# Установка переменных окружения (см. env.production.example)
heroku config:set TELEGRAM_BOT_TOKEN=...
heroku config:set OPENAI_API_KEY=...
# ... и остальные переменные

# Деплой
git push heroku main

# Запуск процессов
heroku ps:scale web=1 bot=1 worker=1
```

## 📁 Структура проекта

```
clientera-telegram-bot/
├── admin/              # Админ-панель (FastAPI)
├── bot/                # Telegram бот
├── core/               # Основные модули (OpenAI, YClients)
├── database/           # Модели базы данных
├── knowledge_base/     # База знаний салона
├── prompts/            # Промпты для GPT
├── templates/          # HTML шаблоны
├── test/               # Тесты [[memory:6483523]]
├── local_development/  # Файлы для локальной разработки
└── to_delete/          # Файлы для проверки и удаления
```

## 🔧 Конфигурация

### Qdrant Cloud
- URL: `https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io`
- Коллекция: `laliq_knowledge_base`
- Размер векторов: 3072 (text-embedding-3-large)

### Heroku
- Приложение: `clientera-telegram-bot`
- Автодеплой: из ветки `main` [[memory:6385103]]
- Процессы:
  - `web`: Админ-панель
  - `bot`: Telegram бот
  - `worker`: Сервис напоминаний

## 📊 Мониторинг

```bash
# Логи
heroku logs --tail

# Статус процессов
heroku ps

# Метрики
heroku metrics
```

## 🔄 Обновление базы знаний

После изменения файлов в `knowledge_base/`:

1. Запустите миграцию данных:
```bash
python migrate_to_qdrant_cloud.py
# Выберите опцию 2
```

2. Проверьте работу:
```bash
heroku logs --tail
```

## 🛠️ Локальная разработка

Все файлы для локальной разработки находятся в папке `local_development/`.
См. [local_development/README.md](local_development/README.md)

## 📝 Документация

- [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) - Подробная инструкция по деплою
- [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) - История изменений
- [env.production.example](env.production.example) - Пример переменных окружения

## ⚠️ Важно

1. **Не коммитьте** файлы `.env`, `.env.production` с реальными ключами
2. **Используйте** Heroku Config Vars для хранения секретов
3. **Проверяйте** логи после деплоя
4. **Тестируйте** бота после каждого обновления

## 🆘 Поддержка

При проблемах проверьте:
1. Логи: `heroku logs --tail`
2. Переменные: `heroku config`
3. Статус БД: `heroku pg:info`
4. Подключение к Qdrant: `python migrate_to_qdrant_cloud.py` (опция 3)
