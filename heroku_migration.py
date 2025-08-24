#!/usr/bin/env python3
"""
Простая миграция для Heroku без SQLAlchemy
"""

import os
import psycopg2
from urllib.parse import urlparse

def run_migration():
    """Выполнить миграцию базы данных на Heroku"""
    print("🔄 Выполнение миграции на Heroku: добавление полей service_ids и staff_id в appointments")

    try:
        # Получаем DATABASE_URL из переменных окружения
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL не найден в переменных окружения")
            return

        print(f"📡 Подключение к базе данных...")

        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("✅ Подключение к базе данных установлено")

        # Проверяем, существуют ли уже поля
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'appointments'
            AND column_name IN ('service_ids', 'staff_id')
        """)

        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Существующие поля: {existing_columns}")

        # Добавляем поля, если их нет
        if 'service_ids' not in existing_columns:
            print("📋 Добавляем поле service_ids...")
            cursor.execute("ALTER TABLE appointments ADD COLUMN service_ids VARCHAR")
            print("✅ Поле service_ids добавлено")
        else:
            print("ℹ️ Поле service_ids уже существует")

        if 'staff_id' not in existing_columns:
            print("👨‍💼 Добавляем поле staff_id...")
            cursor.execute("ALTER TABLE appointments ADD COLUMN staff_id INTEGER")
            print("✅ Поле staff_id добавлено")
        else:
            print("ℹ️ Поле staff_id уже существует")

        # Подтверждаем изменения
        conn.commit()
        print("💾 Изменения сохранены в базе данных")

        # Проверяем структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'appointments'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        print("\n📊 Структура таблицы appointments:")
        for col in columns:
            print(f"   {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

        # Закрываем соединение
        cursor.close()
        conn.close()

        print("\n🎉 Миграция успешно завершена!")

    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
