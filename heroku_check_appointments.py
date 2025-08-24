#!/usr/bin/env python3
"""
Проверка записей в таблице appointments на Heroku
"""

import os
import psycopg2
from urllib.parse import urlparse

def check_appointments():
    """Проверить записи в таблице appointments"""
    try:
        print("🔍 Проверка записей в таблице appointments на Heroku...")

        # Получаем DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL не найден в переменных окружения")
            return

        print(f"📡 Подключение к базе данных...")

        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("✅ Подключение к базе данных установлено")

        # Проверяем структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'appointments'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        print(f"\n📊 Структура таблицы appointments:")
        for col in columns:
            print(f"   {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM appointments")
        count = cursor.fetchone()[0]
        print(f"\n📋 Общее количество записей: {count}")

        if count > 0:
            # Показываем последние 5 записей
            cursor.execute("""
                SELECT id, client_id, service_name, master_name, appointment_datetime, status, created_at
                FROM appointments
                ORDER BY created_at DESC
                LIMIT 5
            """)

            appointments = cursor.fetchall()
            print(f"\n📝 Последние {len(appointments)} записей:")

            for app in appointments:
                print(f"\n   🆔 ID: {app[0]}")
                print(f"   👤 Клиент ID: {app[1]}")
                print(f"   🛠️ Услуга: {app[2]}")
                print(f"   👨‍💼 Мастер: {app[3]}")
                print(f"   📅 Дата: {app[4]}")
                print(f"   📊 Статус: {app[5]}")
                print(f"   🕐 Создано: {app[6]}")

                # Проверяем новые поля, если они есть
                try:
                    cursor.execute("SELECT service_ids, staff_id FROM appointments WHERE id = %s", (app[0],))
                    new_fields = cursor.fetchone()
                    if new_fields:
                        print(f"   🔗 ID услуг: {new_fields[0]}")
                        print(f"   🔗 ID мастера: {new_fields[1]}")
                except Exception as e:
                    print(f"   ⚠️ Новые поля недоступны: {e}")
        else:
            print("📭 Записей в таблице нет")

        # Закрываем соединение
        cursor.close()
        conn.close()

        print("\n🎉 Проверка завершена!")

    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_appointments()
