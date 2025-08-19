#!/bin/bash

# Скрипт для деплоя на Heroku
# Использование: ./deploy_to_heroku.sh

echo "🚀 Начинаем деплой на Heroku..."

# Проверка наличия Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI не установлен. Установите его с https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Проверка авторизации в Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Вы не авторизованы в Heroku. Выполните: heroku login"
    exit 1
fi

APP_NAME="clientera-telegram-bot"

# Проверка существования приложения
if ! heroku apps:info --app $APP_NAME &> /dev/null; then
    echo "📱 Создаем приложение $APP_NAME..."
    heroku create $APP_NAME
else
    echo "✅ Приложение $APP_NAME уже существует"
fi

# Установка buildpack
echo "📦 Устанавливаем Python buildpack..."
heroku buildpacks:set heroku/python --app $APP_NAME

# Проверка наличия PostgreSQL
if ! heroku addons --app $APP_NAME | grep -q "heroku-postgresql"; then
    echo "🗄️ Добавляем PostgreSQL..."
    heroku addons:create heroku-postgresql:mini --app $APP_NAME
else
    echo "✅ PostgreSQL уже подключен"
fi

# Установка переменных окружения
echo "🔧 Настройка переменных окружения..."
echo "Пожалуйста, убедитесь, что вы настроили переменные окружения в Heroku Dashboard или используя команды из HEROKU_DEPLOYMENT.md"

# Добавление git remote если его нет
if ! git remote | grep -q "heroku"; then
    echo "🔗 Добавляем Heroku remote..."
    heroku git:remote --app $APP_NAME
fi

# Коммит изменений
echo "💾 Подготовка к деплою..."
git add .
git commit -m "Deploy to Heroku $(date +%Y-%m-%d_%H:%M:%S)" || echo "Нет изменений для коммита"

# Деплой
echo "🚀 Деплой на Heroku..."
git push heroku main

# Запуск процессов
echo "⚙️ Запуск процессов..."
heroku ps:scale web=1 bot=1 worker=1 --app $APP_NAME

# Загрузка базы знаний
echo "📚 Загрузка базы знаний в Qdrant Cloud..."
heroku run python load_knowledge_base.py --app $APP_NAME

# Проверка статуса
echo "📊 Проверка статуса..."
heroku ps --app $APP_NAME

echo "✅ Деплой завершен!"
echo "📱 Telegram бот: проверьте работу бота в Telegram"
echo "🌐 Админ-панель: https://$APP_NAME.herokuapp.com"
echo "📋 Логи: heroku logs --tail --app $APP_NAME"
echo ""
echo "🔍 Для проверки базы знаний выполните:"
echo "heroku run python -c \"import asyncio; from bot.embedding import EmbeddingService; print('Тестируем поиск...'); service = EmbeddingService(); results = asyncio.run(service.search_similar('маникюр')); print(f'Найдено {len(results)} результатов')\" --app $APP_NAME"
