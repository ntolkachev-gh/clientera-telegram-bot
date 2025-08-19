"""
Тесты для метода get_available_days YClients API
"""
import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from core.yclients_client import YclientsClient
from config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGetAvailableDays:
    """Тесты для get_available_days"""

    @pytest.fixture
    def yclients_client(self):
        """Создание клиента YClients для тестов"""
        return YclientsClient(
            api_key=settings.yclients_api_key,
            company_id=settings.yclients_company_id
        )

    @pytest.mark.asyncio
    async def test_get_available_days_with_valid_params(self, yclients_client):
        """Тест получения доступных дней с корректными параметрами"""
        logger.info("🧪 Тестируем get_available_days с корректными параметрами")

        # Используем реальные ID из вашей системы
        staff_id = 4244041  # ID реального сотрудника
        service_id = 9128038  # ID реальной услуги

        result = await yclients_client.get_available_days(
            staff_id=staff_id,
            service_id=service_id
        )

        logger.info(f"📅 Результат get_available_days: {result}")

        # Проверяем структуру ответа
        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'data' in result, "В результате должен быть ключ 'data'"
        assert 'booking_dates' in result['data'], "В data должен быть ключ 'booking_dates'"

        booking_dates = result['data']['booking_dates']
        assert isinstance(booking_dates, list), "booking_dates должен быть списком"

        logger.info(f"✅ Найдено {len(booking_dates)} доступных дней")

        # Если есть доступные дни, проверяем их формат
        if booking_dates:
            first_date = booking_dates[0]
            logger.info(f"📅 Первая доступная дата: {first_date}")

            # Проверяем, что дата в корректном формате
            if isinstance(first_date, (int, float)):
                # Если это timestamp, проверяем что он валидный
                try:
                    date_obj = datetime.fromtimestamp(first_date)
                    logger.info(f"📅 Дата как timestamp: {date_obj.strftime('%Y-%m-%d')}")
                    assert date_obj.year >= 2024, "Дата должна быть не в прошлом"
                except (ValueError, OSError) as e:
                    pytest.fail(f"Некорректный timestamp: {first_date}, ошибка: {e}")
            elif isinstance(first_date, str):
                # Если это строка, проверяем формат
                try:
                    date_obj = datetime.strptime(first_date, '%Y-%m-%d')
                    logger.info(f"📅 Дата как строка: {date_obj.strftime('%Y-%m-%d')}")
                    assert date_obj.year >= 2024, "Дата должна быть не в прошлом"
                except ValueError as e:
                    pytest.fail(f"Некорректный формат даты: {first_date}, ошибка: {e}")

    @pytest.mark.asyncio
    async def test_get_available_days_with_invalid_staff_id(self, yclients_client):
        """Тест с несуществующим ID сотрудника"""
        logger.info("🧪 Тестируем get_available_days с несуществующим staff_id")

        staff_id = 999999999  # Несуществующий ID
        service_id = 9128038  # Реальный ID услуги

        result = await yclients_client.get_available_days(
            staff_id=staff_id,
            service_id=service_id
        )

        logger.info(f"📅 Результат с несуществующим staff_id: {result}")

        # API должен вернуть пустой список или ошибку
        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'data' in result, "В результате должен быть ключ 'data'"

        booking_dates = result['data'].get('booking_dates', [])
        assert isinstance(booking_dates, list), "booking_dates должен быть списком"

        # Ожидаем пустой список для несуществующего сотрудника
        logger.info(f"✅ Для несуществующего сотрудника получено {len(booking_dates)} дней")

    @pytest.mark.asyncio
    async def test_get_available_days_with_invalid_service_id(self, yclients_client):
        """Тест с несуществующим ID услуги"""
        logger.info("🧪 Тестируем get_available_days с несуществующим service_id")

        staff_id = 4244041  # Реальный ID сотрудника
        service_id = 999999999  # Несуществующий ID

        result = await yclients_client.get_available_days(
            staff_id=staff_id,
            service_id=service_id
        )

        logger.info(f"📅 Результат с несуществующим service_id: {result}")

        # API должен вернуть пустой список или ошибку
        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'data' in result, "В результате должен быть ключ 'data'"

        booking_dates = result['data'].get('booking_dates', [])
        assert isinstance(booking_dates, list), "booking_dates должен быть списком"

        # Ожидаем пустой список для несуществующей услуги
        logger.info(f"✅ Для несуществующей услуги получено {len(booking_dates)} дней")

    @pytest.mark.asyncio
    async def test_get_available_days_multiple_calls(self, yclients_client):
        """Тест множественных вызовов для проверки стабильности"""
        logger.info("🧪 Тестируем множественные вызовы get_available_days")

        staff_id = 4244041
        service_id = 9128038

        results = []
        for i in range(3):
            logger.info(f"📞 Вызов #{i+1}")
            result = await yclients_client.get_available_days(
                staff_id=staff_id,
                service_id=service_id
            )
            results.append(result)

            # Небольшая пауза между вызовами
            await asyncio.sleep(0.5)

        # Проверяем, что все вызовы вернули корректную структуру
        for i, result in enumerate(results):
            logger.info(f"📊 Результат вызова #{i+1}: {len(result['data'].get('booking_dates', []))} дней")
            assert isinstance(result, dict), f"Результат {i+1} должен быть словарем"
            assert 'data' in result, f"В результате {i+1} должен быть ключ 'data'"
            assert 'booking_dates' in result['data'], f"В data результата {i+1} должен быть ключ 'booking_dates'"

        logger.info("✅ Все множественные вызовы прошли успешно")


if __name__ == "__main__":
    # Запуск тестов напрямую
    async def run_tests():
        test_instance = TestGetAvailableDays()
        client = YclientsClient(
            api_key=settings.yclients_api_key,
            company_id=settings.yclients_company_id
        )

        logger.info("🚀 Запуск тестов get_available_days...")

        try:
            await test_instance.test_get_available_days_with_valid_params(client)
            await test_instance.test_get_available_days_with_invalid_staff_id(client)
            await test_instance.test_get_available_days_with_invalid_service_id(client)
            await test_instance.test_get_available_days_multiple_calls(client)

            logger.info("🎉 Все тесты get_available_days прошли успешно!")

        except Exception as e:
            logger.error(f"❌ Ошибка в тестах: {e}")
            raise

    # Запуск
    asyncio.run(run_tests())
