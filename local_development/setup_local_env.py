#!/usr/bin/env python3
"""
Скрипт для настройки локального окружения
"""

import os
import sys

def create_env_file():
    """Создает файл .env с переменными окружения"""

    print("🔧 Настройка локального окружения для бота")
    print("=" * 50)

    # Проверяем, существует ли уже .env файл
    if os.path.exists('.env'):
        print("⚠️ Файл .env уже существует!")
        response = input("Перезаписать? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Настройка отменена")
            return False

    print("\n📝 Введите значения для переменных окружения:")
    print("(Оставьте пустым, если не знаете значение)")

    env_vars = {}

    # Telegram Bot
    print("\n🤖 TELEGRAM BOT:")
    env_vars['TELEGRAM_BOT_TOKEN'] = input("TELEGRAM_BOT_TOKEN: ").strip()

    # OpenAI
    print("\n🧠 OPENAI:")
    env_vars['OPENAI_API_KEY'] = input("OPENAI_API_KEY: ").strip()

    # Qdrant Cloud
    print("\n🔍 QDRANT:")
    env_vars['QDRANT_URL'] = input("QDRANT_URL: ").strip()
    env_vars['QDRANT_API_KEY'] = input("QDRANT_API_KEY: ").strip()

    # PostgreSQL
    print("\n🗄️ DATABASE:")
    env_vars['DATABASE_URL'] = input("DATABASE_URL: ").strip()

    # Youclients API
    print("\n📊 YOUCLIENTS:")
    env_vars['YOUCLIENTS_API_KEY'] = input("YOUCLIENTS_API_KEY: ").strip()
    env_vars['YOUCLIENTS_COMPANY_ID'] = input("YOUCLIENTS_COMPANY_ID: ").strip()

    # Admin settings
    print("\n👑 ADMIN:")
    env_vars['ADMIN_SECRET_KEY'] = input("ADMIN_SECRET_KEY: ").strip()
    env_vars['ADMIN_USERNAME'] = input("ADMIN_USERNAME (по умолчанию 'admin'): ").strip() or 'admin'
    env_vars['ADMIN_PASSWORD'] = input("ADMIN_PASSWORD: ").strip()

    # App settings
    print("\n⚙️ APP SETTINGS:")
    env_vars['DEBUG'] = input("DEBUG (true/false, по умолчанию true): ").strip() or 'true'
    env_vars['REMIND_AFTER_DAYS'] = input("REMIND_AFTER_DAYS (по умолчанию 21): ").strip() or '21'
    env_vars['SESSION_TIMEOUT_HOURS'] = input("SESSION_TIMEOUT_HOURS (по умолчанию 6): ").strip() or '6'

    # Создаем .env файл
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            for key, value in env_vars.items():
                if value:  # Записываем только непустые значения
                    f.write(f"{key}={value}\n")

        print(f"\n✅ Файл .env создан успешно!")
        print(f"📁 Путь: {os.path.abspath('.env')}")

        # Показываем статистику
        filled_vars = sum(1 for v in env_vars.values() if v)
        total_vars = len(env_vars)
        print(f"📊 Заполнено переменных: {filled_vars}/{total_vars}")

        if filled_vars < total_vars:
            print("⚠️ Некоторые переменные не заполнены. Бот может работать неполноценно.")

        return True

    except Exception as e:
        print(f"❌ Ошибка при создании .env файла: {e}")
        return False

def validate_env():
    """Проверяет корректность .env файла"""
    print("\n🔍 Проверка .env файла...")

    if not os.path.exists('.env'):
        print("❌ Файл .env не найден")
        return False

    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = [
            'OPENAI_API_KEY',
            'QDRANT_URL',
            'QDRANT_API_KEY',
            'DATABASE_URL',
            'YOUCLIENTS_API_KEY',
            'YOUCLIENTS_COMPANY_ID'
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"⚠️ Отсутствуют важные переменные: {', '.join(missing_vars)}")
            print("💡 Бот может работать неполноценно")
        else:
            print("✅ Все важные переменные настроены")

        return True

    except ImportError:
        print("❌ python-dotenv не установлен. Установите: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Настройка локального окружения для бота")
    print("=" * 50)

    # Создаем .env файл
    if create_env_file():
        print("\n" + "=" * 50)

        # Проверяем .env файл
        validate_env()

        print("\n🎉 Настройка завершена!")
        print("\n📋 Следующие шаги:")
        print("1. Убедитесь, что PostgreSQL запущен")
        print("2. Запустите локальный бот: python3 local_test.py")
        print("3. Откройте http://localhost:5001 в браузере")

        print("\n💡 Для изменения настроек запустите скрипт снова")

    else:
        print("\n❌ Настройка не завершена")
        print("💡 Проверьте права доступа к папке")

if __name__ == "__main__":
    main()

