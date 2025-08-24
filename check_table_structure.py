#!/usr/bin/env python3
"""
Проверка структуры таблицы appointments на Heroku
"""

from database.database import get_db
from database.models import Appointment

def check_table_structure():
    """Проверить структуру таблицы appointments"""
    try:
        print("🔍 Проверка структуры таблицы appointments...")

        db = next(get_db())

        # Получаем информацию о колонках
        columns = Appointment.__table__.columns
        print(f"\n📊 Структура таблицы appointments:")

        for column in columns:
            nullable = "NULL" if column.nullable else "NOT NULL"
            print(f"   {column.name}: {column.type} ({nullable})")

        # Проверяем наличие нужных полей
        column_names = [c.name for c in columns]

        print(f"\n✅ Проверка наличия новых полей:")
        if 'service_ids' in column_names:
            print("   ✅ service_ids - присутствует")
        else:
            print("   ❌ service_ids - отсутствует")

        if 'staff_id' in column_names:
            print("   ✅ staff_id - присутствует")
        else:
            print("   ❌ staff_id - отсутствует")

        # Проверяем существующие записи
        appointments_count = db.query(Appointment).count()
        print(f"\n📋 Количество записей в таблице: {appointments_count}")

        if appointments_count > 0:
            # Показываем пример записи
            sample = db.query(Appointment).first()
            print(f"\n📝 Пример записи:")
            print(f"   ID: {sample.id}")
            print(f"   Клиент ID: {sample.client_id}")
            print(f"   Услуга: {sample.service_name}")
            print(f"   Мастер: {sample.master_name}")
            print(f"   Дата: {sample.appointment_datetime}")

            # Проверяем новые поля
            if hasattr(sample, 'service_ids'):
                print(f"   ID услуг: {sample.service_ids}")
            else:
                print(f"   ID услуг: поле отсутствует")

            if hasattr(sample, 'staff_id'):
                print(f"   ID мастера: {sample.staff_id}")
            else:
                print(f"   ID мастера: поле отсутствует")

        db.close()

    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure()
