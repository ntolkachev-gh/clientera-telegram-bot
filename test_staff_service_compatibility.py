#!/usr/bin/env python3
"""
Тестирование совместимости мастеров и услуг в YClients API
Проверяет какие мастера могут выполнять какие услуги
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Добавляем корневую папку в путь для импортов
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from core.yclients_client import YclientsClient
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_staff_service_compatibility():
    """Тестирование совместимости мастеров и услуг"""
    try:
        logger.info("🧪 Тестируем совместимость мастеров и услуг...")

        # Создаем клиент
        yclients = YclientsClient(
            api_key=settings.youclients_api_key,
            company_id=settings.youclients_company_id
        )

        # Получаем список мастеров
        logger.info("👥 Получаем список мастеров...")
        staff_list = await yclients.get_staff()
        logger.info(f"Найдено мастеров: {len(staff_list)}")

        # Получаем список услуг
        logger.info("📋 Получаем список услуг...")
        services_list = await yclients.get_services()
        logger.info(f"Найдено услуг: {len(services_list)}")

        # Тестируем совместимость
        compatibility_matrix = {}

        # Берем первых 3 мастеров и первые 5 услуг для тестирования
        test_staff = staff_list[:3]
        test_services = services_list[:5]

        logger.info(f"🔍 Тестируем совместимость {len(test_staff)} мастеров с {len(test_services)} услугами...")

        for staff in test_staff:
            staff_id = staff.id
            staff_name = staff.name
            logger.info(f"\n👤 Тестируем мастера: {staff_name} (ID: {staff_id})")

            compatibility_matrix[staff_id] = {
                'name': staff_name,
                'compatible_services': [],
                'incompatible_services': []
            }

            for service in test_services:
                service_id = service.id
                service_title = service.title

                logger.info(f"  🔍 Проверяем услугу: {service_title} (ID: {service_id})")

                # Тестируем get_available_days
                result = await yclients.get_available_days(staff_id=staff_id, service_id=service_id)

                if 'error' in result and result.get('error_code') == 'STAFF_UNAVAILABLE':
                    logger.info(f"    ❌ Недоступно: {result['error']}")
                    compatibility_matrix[staff_id]['incompatible_services'].append({
                        'service_id': service_id,
                        'service_title': service_title,
                        'error': result['error']
                    })
                elif 'error' in result:
                    logger.info(f"    ⚠️ Ошибка: {result['error']}")
                    compatibility_matrix[staff_id]['incompatible_services'].append({
                        'service_id': service_id,
                        'service_title': service_title,
                        'error': result['error']
                    })
                else:
                    days_count = len(result['data'].get('booking_dates', []))
                    logger.info(f"    ✅ Доступно ({days_count} дней)")
                    compatibility_matrix[staff_id]['compatible_services'].append({
                        'service_id': service_id,
                        'service_title': service_title,
                        'available_days': days_count
                    })

        # Выводим результаты
        logger.info("\n" + "="*60)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СОВМЕСТИМОСТИ")
        logger.info("="*60)

        for staff_id, data in compatibility_matrix.items():
            logger.info(f"\n👤 {data['name']} (ID: {staff_id})")

            compatible = data['compatible_services']
            incompatible = data['incompatible_services']

            logger.info(f"  ✅ Совместимых услуг: {len(compatible)}")
            for service in compatible:
                logger.info(f"    - {service['service_title']} ({service['available_days']} дней)")

            logger.info(f"  ❌ Несовместимых услуг: {len(incompatible)}")
            for service in incompatible:
                logger.info(f"    - {service['service_title']}: {service['error']}")

        logger.info("\n" + "="*60)
        logger.info("💡 РЕКОМЕНДАЦИИ")
        logger.info("="*60)

        # Находим универсальных мастеров
        universal_masters = []
        for staff_id, data in compatibility_matrix.items():
            if len(data['compatible_services']) >= 3:
                universal_masters.append(data['name'])

        if universal_masters:
            logger.info(f"🌟 Универсальные мастера (3+ услуг): {', '.join(universal_masters)}")

        # Находим проблемные услуги
        service_availability = {}
        for staff_id, data in compatibility_matrix.items():
            for service in data['compatible_services']:
                service_title = service['service_title']
                if service_title not in service_availability:
                    service_availability[service_title] = 0
                service_availability[service_title] += 1

        unavailable_services = []
        for service in test_services:
            if service.title not in service_availability:
                unavailable_services.append(service.title)

        if unavailable_services:
            logger.info(f"⚠️ Услуги без доступных мастеров: {', '.join(unavailable_services)}")

        return compatibility_matrix

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return None


async def main():
    """Основная функция"""
    print("🧪 Тестирование совместимости мастеров и услуг")
    print("=" * 50)

    # Проверяем конфигурацию
    logger.info(f"🔧 YClients Company ID: {settings.youclients_company_id}")
    logger.info(f"🔧 YClients API Key: {'*' * 20}...{settings.youclients_api_key[-10:] if settings.youclients_api_key else 'НЕ УСТАНОВЛЕН'}")

    # Запускаем тестирование
    result = await test_staff_service_compatibility()

    print("\n" + "=" * 50)
    if result:
        print("🎉 Тестирование завершено!")
        print("📋 Результаты выведены в логи выше.")
        print("💡 Используйте эту информацию для правильного сопоставления мастеров и услуг.")
    else:
        print("❌ Тестирование не удалось!")
        print("🔍 Проверьте настройки API и подключение.")
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
