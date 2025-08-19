#!/usr/bin/env python3
"""
Скрипт для запуска локального тестирования бота
"""

import os
import sys
import subprocess

def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    try:
        import flask
        print("✅ Flask установлен")
    except ImportError:
        print("❌ Flask не установлен. Устанавливаем...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask==3.0.0"])
        print("✅ Flask установлен")

def check_env_file():
    """Проверяет наличие .env файла"""
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env с необходимыми переменными окружения:")
        print("""
# Пример .env файла:
TELEGRAM_BOT_TOKEN=your_telegram_token
OPENAI_API_KEY=your_openai_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
DATABASE_URL=your_database_url
YOUCLIENTS_API_KEY=your_youclients_key
YOUCLIENTS_COMPANY_ID=your_company_id
ADMIN_SECRET_KEY=your_admin_secret
ADMIN_PASSWORD=your_admin_password
        """)
        return False
    print("✅ Файл .env найден")
    return True

def main():
    """Основная функция"""
    print("🚀 Запуск локального тестирования бота")
    print("=" * 50)

    # Проверяем зависимости
    check_dependencies()

    # Проверяем .env файл
    if not check_env_file():
        print("\n❌ Не удалось запустить тестирование. Создайте .env файл.")
        return

    print("\n✅ Все проверки пройдены!")
    print("🚀 Запускаем локальный бот...")
    print("\n📱 После запуска откройте http://localhost:5000 в браузере")
    print("💬 Теперь вы можете тестировать бота локально!")
    print("\n" + "=" * 50)

    # Запускаем локальный бот
    try:
        subprocess.run([sys.executable, "local_test.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Локальное тестирование остановлено")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при запуске: {e}")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
