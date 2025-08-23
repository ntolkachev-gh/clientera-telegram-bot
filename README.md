# Clientera - MVP Telegram-бот для записи клиентов

Telegram-бот для салона красоты с поддержкой LLM (OpenAI GPT-5) и векторной базы знаний (Qdrant Cloud). Бот ведёт диалог, запоминает предпочтения клиента, записывает его через API Youclients, и напоминает о повторной записи.

## ⚡ Оптимизация производительности

**Проблема**: Бот работал медленно из-за GPT-5 (20-30 секунд на ответ)

**Решение**: Автоматический выбор быстрых моделей OpenAI
- **GPT-4o-mini**: ~3 секунды (рекомендуется для скорости)
- **GPT-4o**: ~8 секунд (сбалансированный выбор)
- **GPT-5**: ~25 секунд (только для сложных задач)

**Результат**: Ускорение в 4-8 раз! См. [OPENAI_OPTIMIZATION_GUIDE.md](OPENAI_OPTIMIZATION_GUIDE.md)

## 🚀 Функции

- **Умный диалог с клиентом** - естественное общение с помощью GPT-5
- **Интеграция с Youclients** - получение услуг/мастеров и создание записей
- **База знаний** - поиск ответов в Markdown-файлах через Qdrant
- **Профиль клиента** - сохранение предпочтений и истории
- **Напоминания** - автоматические уведомления о повторной записи
- **Админка** - веб-интерфейс для управления клиентами и статистикой

## 🛠 Технологии

- **Python 3.11+**
- **python-telegram-bot** - Telegram Bot API
- **OpenAI API** - GPT-5 и text-embedding-3-small
- **Qdrant Cloud** - векторная база знаний
- **PostgreSQL** - основная база данных
- **FastAPI + Jinja2** - админка
- **Heroku** - развертывание

## 📦 Установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd Clientera
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env` на основе примера:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_DEFAULT_MODEL=gpt-5  # Модель по умолчанию (gpt-5, gpt-4, gpt-4-turbo)

# Qdrant Cloud
QDRANT_URL=your_qdrant_cloud_url_here
QDRANT_API_KEY=your_qdrant_api_key_here

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/clientera_db

# Youclients API
YOUCLIENTS_API_KEY=your_youclients_api_key_here
YOUCLIENTS_COMPANY_ID=your_company_id_here

# Admin settings
ADMIN_SECRET_KEY=your_admin_secret_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password_here

# App settings
DEBUG=False
REMIND_AFTER_DAYS=21
SESSION_TIMEOUT_HOURS=6
```

### 4. Инициализация базы данных
```bash
python -c "from database.database import init_db; init_db()"
```

### 5. Загрузка базы знаний
```bash
python bot/embedding.py
```

## 🚀 Запуск

### Локальный запуск
```bash
# Запуск бота
python bot/main.py

# Запуск админки
python -m uvicorn admin.main:app --reload --port 8000

# Запуск напоминаний (вручную)
python bot/remind.py
```

### Развертывание на Heroku

1. **Создание приложения**
```bash
heroku create your-app-name
```

2. **Добавление PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini
```

3. **Настройка переменных окружения**
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key
# ... остальные переменные
```

4. **Развертывание**
```bash
git push heroku main
```

5. **Инициализация базы данных**
```bash
heroku run python -c "from database.database import init_db; init_db()"
```

6. **Загрузка базы знаний**
```bash
heroku run python bot/embedding.py
```
