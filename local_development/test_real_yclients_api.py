#!/usr/bin/env python3
"""
Тестовый скрипт для проверки реального YClients API
"""
import asyncio
import logging
from datetime import datetime, timedelta
from core.yclients_client import YclientsClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_yclients_api():
    """Тестирование реального YClients API"""

    # Реальные credentials из рабочего cURL
    api_key = "nmnsgmfcpdu65db2b5kp"
    company_id = "1297379"

    logger.info("🚀 Начинаем тестирование реального YClients API")
    logger.info(f"🏢 Компания: {company_id}")
    logger.info(f"🔑 API ключ: {api_key[:10]}...")

    # Создаем клиент
    client = YclientsClient(api_key=api_key, company_id=company_id)

    try:
        # 1. Тестируем получение услуг
        logger.info("\n" + "="*50)
        logger.info("📋 ТЕСТ 1: Получение списка услуг")
        logger.info("="*50)

        services = await client.get_services(use_real_api=True)
        logger.info(f"✅ Получено услуг: {len(services)}")

        if services:
            logger.info("📋 Первые 3 услуги:")
            for service in services[:3]:
                logger.info(f"   • {service.title} - {service.price} руб ({service.duration} мин)")

        # 2. Тестируем получение мастеров
        logger.info("\n" + "="*50)
        logger.info("👥 ТЕСТ 2: Получение списка мастеров")
        logger.info("="*50)

        staff = await client.get_staff(use_real_api=True)
        logger.info(f"✅ Получено мастеров: {len(staff)}")

        if staff:
            logger.info("👥 Первые 3 мастера:")
            for master in staff[:3]:
                logger.info(f"   • {master.name} - {master.specialization}")

        # 3. Тестируем получение временных слотов
        logger.info("\n" + "="*50)
        logger.info("🕒 ТЕСТ 3: Получение временных слотов")
        logger.info("="*50)

        # Используем завтра и послезавтра для тестирования
        tomorrow = datetime.now() + timedelta(days=1)
        day_after = datetime.now() + timedelta(days=2)

        # Используем реальные ID из полученных данных
        test_service_ids = [services[0].id] if services else [19437973]  # ID из API
        test_staff_id = staff[0].id if staff else 4244041  # ID из API

        logger.info(f"🔍 Поиск слотов для услуги {test_service_ids} и мастера {test_staff_id}")
        logger.info(f"📅 Период: {tomorrow.strftime('%Y-%m-%d')} - {day_after.strftime('%Y-%m-%d')}")

        slots = await client.get_available_slots(
            service_ids=test_service_ids,
            date_from=tomorrow,
            date_to=day_after,
            staff_id=test_staff_id,
            use_real_api=True
        )

        logger.info(f"✅ Получено слотов: {len(slots)}")

        if slots:
            logger.info("🕒 Первые 5 слотов:")
            for slot in slots[:5]:
                logger.info(f"   • {slot.start.strftime('%Y-%m-%d %H:%M')} - "
                           f"{slot.end.strftime('%H:%M')} (мастер {slot.staff_id})")

        # 4. Тестируем fallback к мокам
        logger.info("\n" + "="*50)
        logger.info("🎭 ТЕСТ 4: Fallback к мок данным")
        logger.info("="*50)

        mock_slots = await client.get_available_slots(
            service_ids=[1, 2],
            date_from=tomorrow,
            date_to=day_after,
            use_real_api=False  # Принудительно используем моки
        )

        logger.info(f"✅ Получено мок слотов: {len(mock_slots)}")

        if mock_slots:
            logger.info("🎭 Первые 3 мок слота:")
            for slot in mock_slots[:3]:
                logger.info(f"   • {slot.start.strftime('%Y-%m-%d %H:%M')} - "
                           f"{slot.end.strftime('%H:%M')} (мастер {slot.staff_id})")

        logger.info("\n" + "="*50)
        logger.info("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"❌ Ошибка во время тестирования: {e}")
        logger.error(f"🔍 Тип ошибки: {type(e).__name__}")
        raise


if __name__ == "__main__":
    asyncio.run(test_real_yclients_api())
