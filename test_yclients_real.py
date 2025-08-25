#!/usr/bin/env python3
"""
Тест работы с реальным YClients API
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.yclients_client import YclientsClient
from config import settings

async def test_yclients_real():
    """Тест реального API YClients"""
    print("🧪 Тестируем реальный YClients API...")

    try:
        # Создаем клиент
        client = YclientsClient(
            api_key=settings.youclients_api_key,
            company_id=settings.youclients_company_id
        )

        print(f"✅ Клиент создан для компании: {settings.youclients_company_id}")

        # 1. Получаем список услуг
        print("\n📋 Получаем список услуг...")
        services = await client.get_services()
        if services:
            print(f"✅ Найдено услуг: {len(services)}")
            # Показываем первые 3 услуги
            for i, service in enumerate(services[:3]):
                print(f"   {i+1}. {service.title} - {service.price}₽ ({service.duration} мин)")
        else:
            print("❌ Не удалось получить услуги")
            return

        # 2. Получаем список мастеров
        print("\n👥 Получаем список мастеров...")
        staff = await client.get_staff()
        if staff:
            print(f"✅ Найдено мастеров: {len(staff)}")
            # Показываем первых 3 мастеров
            for i, master in enumerate(staff[:3]):
                print(f"   {i+1}. {master.name} (ID: {master.id})")
        else:
            print("❌ Не удалось получить мастеров")
            return

        # 3. Тестируем поиск свободных слотов для первого мастера и первой услуги
        if services and staff:
            print(f"\n🔍 Ищем свободные слоты для мастера '{staff[0].name}' и услуги '{services[0].title}'...")

            # Ищем слоты на завтра
            tomorrow = datetime.now() + timedelta(days=1)
            day_after_tomorrow = tomorrow + timedelta(days=1)

            try:
                # Получаем доступные дни
                available_days = await client.get_available_days(
                    staff_id=staff[0].id,
                    service_id=services[0].id
                )

                if 'error' in available_days:
                    print(f"❌ Ошибка при получении дней: {available_days['error']}")
                else:
                    days = available_days['data'].get('booking_dates', [])
                    print(f"✅ Найдено доступных дней: {len(days)}")

                    if days:
                        # Берем первый доступный день
                        first_day = days[0]
                        print(f"📅 Тестируем день: {first_day}")

                        # Получаем временные слоты для этого дня
                        time_slots = await client.get_available_times(
                            staff_id=staff[0].id,
                            service_id=services[0].id,
                            day=first_day
                        )

                        if 'error' in time_slots:
                            print(f"❌ Ошибка при получении слотов: {time_slots['error']}")
                        else:
                            slots = time_slots['data']
                            print(f"✅ Найдено временных слотов: {len(slots)}")

                            if slots:
                                print("🕐 Первые 5 слотов:")
                                for i, slot in enumerate(slots[:5]):
                                    time_str = slot.get('time', 'N/A')
                                    seance_length = slot.get('seance_length', 0)
                                    print(f"   {i+1}. Время: {time_str}, Длительность: {seance_length} сек")
                            else:
                                print("📭 Нет доступных временных слотов")
                    else:
                        print("📭 Нет доступных дней для записи")

            except Exception as e:
                print(f"❌ Ошибка при поиске слотов: {e}")
                print(f"🔍 Тип ошибки: {type(e).__name__}")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print(f"🔍 Тип ошибки: {type(e).__name__}")

if __name__ == "__main__":
    # Проверяем наличие переменных окружения
    if not settings.youclients_api_key or not settings.youclients_company_id:
        print("❌ Отсутствуют переменные окружения для YClients API")
        print("Убедитесь, что в .env файле указаны:")
        print("YOUCLIENTS_API_KEY=ваш_ключ")
        print("YOUCLIENTS_COMPANY_ID=ваш_id_компании")
        sys.exit(1)

    # Запускаем тест
    asyncio.run(test_yclients_real())


