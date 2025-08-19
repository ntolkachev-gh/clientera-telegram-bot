#!/usr/bin/env python3
"""
Быстрое тестирование бота без полной настройки
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Тестирует базовую функциональность без внешних зависимостей"""
    print("🧪 Тестирование базовой функциональности...")

    try:
        # Проверяем импорты
        print("📦 Проверка импортов...")

        # Базовые модули
        import database.database
        print("✅ База данных: OK")

        import bot.dialog_manager
        print("✅ Менеджер диалогов: OK")

        import bot.embedding
        print("✅ Система эмбеддингов: OK")

        print("\n🎉 Базовая функциональность работает!")
        return True

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_config():
    """Тестирует конфигурацию"""
    print("\n⚙️ Проверка конфигурации...")

    try:
        from config import settings

        # Проверяем наличие критических переменных
        required_vars = [
            'telegram_bot_token',
            'openai_api_key',
            'qdrant_url',
            'qdrant_api_key',
            'database_url',
            'youclients_api_key',
            'youclients_company_id'
        ]

        missing_vars = []
        for var in required_vars:
            try:
                value = getattr(settings, var)
                if not value:
                    missing_vars.append(var)
                else:
                    print(f"✅ {var}: {'*' * min(len(str(value)), 8)}")
            except:
                missing_vars.append(var)

        if missing_vars:
            print(f"\n⚠️ Отсутствуют переменные: {', '.join(missing_vars)}")
            print("📝 Создайте файл .env с этими переменными")
            return False
        else:
            print("\n✅ Все необходимые переменные настроены!")
            return True

    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("\n🗄️ Проверка подключения к базе данных...")

    try:
        from database.database import SessionLocal, init_db

        # Пытаемся инициализировать БД
        init_db()
        print("✅ Инициализация БД: OK")

        # Пытаемся создать сессию
        with SessionLocal() as db:
            print("✅ Подключение к БД: OK")

        return True

    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        print("💡 Убедитесь, что PostgreSQL запущен и доступен")
        return False

def show_quick_start():
    """Показывает инструкции по быстрому запуску"""
    print("\n" + "="*60)
    print("🚀 БЫСТРЫЙ СТАРТ ДЛЯ ЛОКАЛЬНОГО ТЕСТИРОВАНИЯ")
    print("="*60)

    print("\n📋 Шаг 1: Установите зависимости")
    print("   pip install -r requirements.txt")

    print("\n📋 Шаг 2: Создайте файл .env")
    print("   cp .env.example .env  # если есть пример")
    print("   # Или создайте вручную с необходимыми переменными")

    print("\n📋 Шаг 3: Запустите локальный бот")
    print("   python run_local_test.py")

    print("\n📋 Шаг 4: Откройте браузер")
    print("   http://localhost:5000")

    print("\n💡 Альтернативный способ:")
    print("   python local_test.py")

    print("\n🔧 Для тестирования без полной настройки:")
    print("   python quick_test.py")

    print("\n" + "="*60)

def main():
    """Основная функция"""
    print("🤖 Быстрое тестирование бота")
    print("="*40)

    # Тест 1: Базовая функциональность
    basic_ok = test_basic_functionality()

    # Тест 2: Конфигурация
    config_ok = test_config()

    # Тест 3: База данных (если возможно)
    db_ok = False
    if basic_ok and config_ok:
        db_ok = test_database_connection()

    # Результаты
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   Базовая функциональность: {'✅' if basic_ok else '❌'}")
    print(f"   Конфигурация: {'✅' if config_ok else '❌'}")
    print(f"   База данных: {'✅' if db_ok else '❌'}")

    if basic_ok and config_ok and db_ok:
        print("\n🎉 Все тесты пройдены! Бот готов к работе!")
        print("💬 Запустите: python run_local_test.py")
    elif basic_ok and config_ok:
        print("\n⚠️ Бот частично готов. Проблемы с базой данных.")
        print("💡 Проверьте подключение к PostgreSQL")
    else:
        print("\n❌ Есть проблемы с настройкой.")
        print("💡 Следуйте инструкциям ниже:")
        show_quick_start()

    print("\n" + "="*40)

if __name__ == "__main__":
    main()
