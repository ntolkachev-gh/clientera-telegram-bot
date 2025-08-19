#!/bin/bash

# Скрипт для запуска local_bot_web.py с логами

echo "🚀 Запуск local_bot_web.py с логами в реальном времени"
echo "=================================================="

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    echo "💡 Установите Docker Desktop для macOS"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Проверяем, что docker-compose.yml существует
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Файл docker-compose.yml не найден"
    exit 1
fi

# Проверяем, что local_bot_web.py существует
if [ ! -f "local_bot_web.py" ]; then
    echo "❌ Файл local_bot_web.py не найден"
    exit 1
fi

# Останавливаем предыдущие сервисы если они запущены
echo "🛑 Остановка предыдущих сервисов..."
docker-compose down 2>/dev/null

# Запускаем сервисы
echo "🐳 Запуск Docker сервисов..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Ошибка запуска сервисов"
    exit 1
fi

echo "✅ Сервисы запущены"

# Ждем готовности PostgreSQL
echo "⏳ Ожидание готовности PostgreSQL..."
for i in {1..15}; do
    if docker-compose exec -T postgres pg_isready -U bot_user -d bot_db &>/dev/null; then
        echo "✅ PostgreSQL готов!"
        break
    fi
    echo "⏳ Попытка $i/15..."
    sleep 2
done

echo ""
echo "🎉 Сервисы готовы!"
echo "🌐 Веб-интерфейс: http://localhost:8081"
echo "🗄️ PostgreSQL: localhost:5432"
echo "🔍 Qdrant: localhost:6333"
echo "🖥️ PgAdmin: http://localhost:8080 (admin/admin)"
echo ""
echo "📊 Логи в реальном времени (Ctrl+C для остановки):"
echo "=================================================="

# Функция для корректного завершения
cleanup() {
    echo ""
    echo "🛑 Остановка сервисов..."
    docker-compose down
    echo "👋 Сервисы остановлены"
    exit 0
}

# Регистрируем обработчик сигналов
trap cleanup SIGINT SIGTERM

# Запускаем просмотр логов всех сервисов
docker-compose logs -f
