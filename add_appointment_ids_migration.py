#!/usr/bin/env python3
"""
Миграция для добавления полей service_ids и staff_id в таблицу appointments
"""

import os
import sys
from sqlalchemy import create_engine, text
from config import settings

def run_migration():
    """Выполнить миграцию базы данных"""
    print("🔄 Выполнение миграции: добавление полей service_ids и staff_id в appointments")

    try:
        # Создаем подключение к базе данных
        engine = create_engine(settings.database_url)

        with engine.connect() as conn:
            # Проверяем, существуют ли уже поля
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'appointments'
                AND column_name IN ('service_ids', 'staff_id')
            """))
            existing_columns = [row[0] for row in result.fetchall()]

            # Добавляем поля, если их нет
            if 'service_ids' not in existing_columns:
                print("📋 Добавляем поле service_ids...")
                conn.execute(text("ALTER TABLE appointments ADD COLUMN service_ids VARCHAR"))
                conn.commit()
                print("✅ Поле service_ids добавлено")
            else:
                print("ℹ️ Поле service_ids уже существует")

            if 'staff_id' not in existing_columns:
                print("👨‍💼 Добавляем поле staff_id...")
                conn.execute(text("ALTER TABLE appointments ADD COLUMN staff_id INTEGER"))
                conn.commit()
                print("✅ Поле staff_id добавлено")
            else:
                print("ℹ️ Поле staff_id уже существует")

        print("🎉 Миграция успешно завершена!")

    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
