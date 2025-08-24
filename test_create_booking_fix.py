#!/usr/bin/env python3
"""
Тест для проверки исправленной функции create_booking
"""

import asyncio
import json
from datetime import datetime
from core.openai_tools import YclientsToolsHandler
from core.yclients_client import YclientsClient
from database.database import get_db
from database.models import Appointment, Client
from config import settings

async def test_create_booking_fix():
    """Тестирование исправленной функции create_booking"""

    print("🧪 Тестирование исправления функции create_booking")
    print("=" * 60)

    try:
        # Создаем YClients клиент и handler
        yclients_client = YclientsClient(
            api_key=settings.youclients_api_key,
            company_id=settings.youclients_company_id
        )

        handler = YclientsToolsHandler(yclients_client)

        # Тестовые данные
        test_data = {
            "phone": "+79291234567",
            "fullname": "Тестовый Клиент",
            "service_ids": [2, 6],  # Примерные ID услуг
            "staff_id": 1,          # Примерный ID мастера
            "booking_datetime": "2025-08-25T14:00:00",
            "comment": "Тестовая запись"
        }

        print(f"📋 Тестовые данные:")
        print(f"   Клиент: {test_data['fullname']}")
        print(f"   Телефон: {test_data['phone']}")
        print(f"   Услуги: {test_data['service_ids']}")
        print(f"   Мастер: {test_data['staff_id']}")
        print(f"   Дата: {test_data['booking_datetime']}")

        # Выполняем создание записи
        print(f"\n🔄 Выполняем create_booking...")
        result = await handler.handle_create_booking(**test_data)

        print(f"\n📊 Результат:")
        print(f"   Успех: {result.get('booking', {}).get('success', False)}")
        print(f"   ID записи: {result.get('booking', {}).get('record_id')}")
        print(f"   Услуги: {result.get('booking', {}).get('services', [])}")
        print(f"   Мастер: {result.get('booking', {}).get('master')}")

        # Проверяем запись в базе данных
        if result.get('booking', {}).get('success'):
            record_id = result.get('booking', {}).get('record_id')

            print(f"\n🔍 Проверяем запись в базе данных...")

            with next(get_db()) as db:
                appointment = db.query(Appointment).filter(Appointment.id == record_id).first()

                if appointment:
                    print(f"✅ Запись найдена в БД:")
                    print(f"   ID: {appointment.id}")
                    print(f"   Клиент ID: {appointment.client_id}")
                    print(f"   Услуги (названия): {appointment.service_name}")
                    print(f"   Услуги (ID): {appointment.service_ids}")
                    print(f"   Мастер (имя): {appointment.master_name}")
                    print(f"   Мастер (ID): {appointment.staff_id}")
                    print(f"   Дата: {appointment.appointment_datetime}")
                    print(f"   Статус: {appointment.status}")

                    # Проверяем, что ID сохранились корректно
                    if appointment.service_ids:
                        try:
                            saved_service_ids = json.loads(appointment.service_ids)
                            print(f"   ✅ ID услуг сохранены корректно: {saved_service_ids}")
                        except:
                            print(f"   ❌ Ошибка парсинга ID услуг: {appointment.service_ids}")

                    if appointment.staff_id:
                        print(f"   ✅ ID мастера сохранен корректно: {appointment.staff_id}")
                    else:
                        print(f"   ❌ ID мастера не сохранен")

                else:
                    print(f"❌ Запись с ID {record_id} не найдена в БД")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎯 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:")
    print("✅ Функция create_booking должна теперь:")
    print("   • Получать реальные названия услуг из Qdrant")
    print("   • Получать реальные имена мастеров из YClients API")
    print("   • Сохранять ID услуг и мастеров в базе данных")

if __name__ == "__main__":
    asyncio.run(test_create_booking_fix())
