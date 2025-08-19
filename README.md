# Clientera - MVP Telegram-бот для записи клиентов

Telegram-бот для салона красоты с поддержкой LLM (OpenAI GPT-5) и векторной базы знаний (Qdrant Cloud). Бот ведёт диалог, запоминает предпочтения клиента, записывает его через API Youclients, и напоминает о повторной записи.

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

7. **Настройка планировщика для напоминаний**
```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler
```
Добавьте задачу: `python bot/remind.py` с частотой "Daily"

## 📁 Структура проекта

```
Clientera/
├── bot/
│   ├── main.py              # Telegram-бот
│   ├── remind.py            # Система напоминаний
│   ├── embedding.py         # Работа с базой знаний
│   ├── dialog_manager.py    # Управление диалогом
│   ├── openai_client.py     # OpenAI API
│   └── youclients_api.py    # Youclients API
├── database/
│   ├── models.py            # SQLAlchemy модели
│   └── database.py          # Настройка БД
├── admin/
│   ├── main.py              # FastAPI админка
│   └── templates/           # HTML шаблоны
├── knowledge_base/          # Markdown файлы
├── config.py                # Настройки
├── requirements.txt         # Зависимости
├── Procfile                 # Heroku конфигурация
├── runtime.txt              # Версия Python
└── README.md
```

## 📚 База знаний

Создайте Markdown файлы в папке `knowledge_base/` со структурой:

```markdown
# Название файла

## Заголовок раздела 1
Содержимое раздела...

## Заголовок раздела 2
Содержимое раздела...
```

Каждый раздел с заголовком `##` будет отдельным чанком в векторной базе.

## 🔧 API Endpoints (Админка)

- `GET /` - Главная страница с статистикой
- `GET /clients` - Список клиентов
- `GET /clients/{id}` - Детали клиента
- `GET /sessions/{id}` - Детали сессии
- `GET /usage` - Статистика OpenAI
- `GET /appointments` - Список записей
- `GET /analytics` - Аналитика

## 🤖 Команды бота

- `/start` - Главное меню
- `/help` - Справка
- `/services` - Список услуг
- `/masters` - Список мастеров
- `/profile` - Профиль пользователя

## 📊 Модели данных

### Client
- Telegram ID, имя, телефон
- Предпочитаемые услуги, мастера, время
- Дата последнего визита
- Настройки напоминаний

### Message
- Содержимое сообщения
- Тип (пользователь/бот)
- Привязка к клиенту и сессии

### OpenAIUsageLog
- Модель, назначение
- Количество токенов
- Стоимость в USD

### Appointment
- Детали записи
- Статус (запланировано/выполнено/отменено)
- Привязка к клиенту

## 🔐 Безопасность

- HTTP Basic Auth для админки
- Валидация входных данных
- Безопасное хранение API ключей
- Логирование всех операций

## 📈 Мониторинг

- Логирование использования OpenAI
- Статистика активности клиентов
- Отслеживание стоимости AI запросов
- Аналитика сессий и сообщений

## 🚨 Troubleshooting

### Проблема: Бот не отвечает
- Проверьте токен Telegram бота
- Убедитесь, что бот запущен
- Проверьте логи приложения

### Проблема: Ошибки OpenAI
- Проверьте API ключ OpenAI
- Убедитесь в наличии средств на счету
- Проверьте лимиты использования

### Проблема: База знаний не работает
- Проверьте подключение к Qdrant
- Убедитесь, что файлы загружены
- Проверьте формат Markdown файлов

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи приложения
2. Убедитесь в правильности настроек
3. Проверьте статус внешних сервисов

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.
