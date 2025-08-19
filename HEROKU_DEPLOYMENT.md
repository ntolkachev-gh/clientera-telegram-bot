# Инструкция по деплою на Heroku

## Предварительные требования

1. Аккаунт на Heroku
2. Установленный Heroku CLI
3. Настроенный Git репозиторий

## Конфигурация

### 1. Qdrant Cloud

Проект настроен для работы с Qdrant Cloud:
- URL: `https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io`
- API Key: Хранится в переменных окружения

### 2. Переменные окружения Heroku

Установите следующие переменные окружения в Heroku:

```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_telegram_bot_token
heroku config:set OPENAI_API_KEY=your_openai_api_key
heroku config:set OPENAI_DEFAULT_MODEL=gpt-5
heroku config:set QDRANT_URL=https://de7ffdf5-270e-466f-bb1b-fd1ca4bbdd8b.us-east4-0.gcp.cloud.qdrant.io
heroku config:set QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DyEayIWfHhpQMYuj0wwNMxpphMN6imYuvVldk02zIkM
heroku config:set YOUCLIENTS_API_KEY=your_youclients_api_key
heroku config:set YOUCLIENTS_COMPANY_ID=your_company_id
heroku config:set ADMIN_SECRET_KEY=your_secret_key
heroku config:set ADMIN_USERNAME=admin
heroku config:set ADMIN_PASSWORD=your_admin_password
heroku config:set DEBUG=False
heroku config:set REMIND_AFTER_DAYS=21
heroku config:set SESSION_TIMEOUT_HOURS=6
```

### 3. База данных PostgreSQL

Heroku автоматически предоставит переменную `DATABASE_URL` при добавлении Heroku Postgres:

```bash
heroku addons:create heroku-postgresql:mini
```

## Миграция данных в Qdrant Cloud

### Вариант 1: Миграция из локального Qdrant

Если у вас есть данные в локальном Qdrant:

```bash
python migrate_to_qdrant_cloud.py
# Выберите опцию 1
```

### Вариант 2: Загрузка из файлов knowledge base

```bash
python migrate_to_qdrant_cloud.py
# Выберите опцию 2
```

## Деплой на Heroku

### 1. Создание приложения

```bash
heroku create clientera-telegram-bot
```

### 2. Добавление buildpack для Python

```bash
heroku buildpacks:set heroku/python
```

### 3. Деплой

```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### 4. Запуск процессов

```bash
# Запуск веб-интерфейса администратора
heroku ps:scale web=1

# Запуск Telegram бота
heroku ps:scale bot=1

# Запуск воркера для напоминаний
heroku ps:scale worker=1
```

## Проверка работы

### 1. Проверка логов

```bash
heroku logs --tail
```

### 2. Проверка статуса процессов

```bash
heroku ps
```

### 3. Доступ к админ-панели

```
https://clientera-telegram-bot.herokuapp.com
```

## Структура проекта

- **Production файлы** - в корне проекта
- **Локальные файлы разработки** - в папке `local_development/`
- **Тесты** - в папке `test/`
- **База знаний** - в папке `knowledge_base/`

## Procfile

Определяет процессы для Heroku:
- `web`: Админ-панель (FastAPI)
- `bot`: Telegram бот
- `worker`: Сервис напоминаний

## Важные замечания

1. **Qdrant Cloud**: Все векторные данные хранятся в облаке, не требуется локальный Qdrant
2. **PostgreSQL**: База данных для хранения диалогов и клиентов предоставляется Heroku
3. **Автодеплой**: Настроен автоматический деплой из ветки `main` (master)
4. **Локальная разработка**: Все файлы для локальной разработки перемещены в `local_development/`

## Мониторинг

### Метрики Heroku

```bash
heroku metrics
```

### Проверка использования ресурсов

```bash
heroku ps:type
```

## Откат изменений

В случае проблем можно откатиться на предыдущую версию:

```bash
heroku releases
heroku rollback v<номер_версии>
```

## Поддержка

При возникновении проблем проверьте:
1. Логи приложения: `heroku logs --tail`
2. Статус переменных окружения: `heroku config`
3. Статус аддонов: `heroku addons`
4. Подключение к Qdrant Cloud через скрипт миграции
