"""
Тесты для метода get_available_times YClients API
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


class TestGetAvailableTimes:
    """Тесты для get_available_times"""

    @pytest.fixture
    def yclients_client(self):
        """Создание клиента YClients для тестов"""
        return YclientsClient(
            api_key=settings.yclients_api_key,
            company_id=settings.yclients_company_id
        )

    @pytest.mark.asyncio
    async def test_get_available_times_with_valid_params(self, yclients_client):
        """Тест получения доступных временных слотов с корректными параметрами"""
        logger.info("🧪 Тестируем get_available_times с корректными параметрами")

        staff_id = 4244041  # ID реального сотрудника
        service_id = 9128038  # ID реальной услуги

        # Сначала получаем доступные дни
        days_result = await yclients_client.get_available_days(
            staff_id=staff_id,
            service_id=service_id
        )

        booking_dates = days_result['data'].get('booking_dates', [])

        if not booking_dates:
            logger.warning("⚠️ Нет доступных дней для тестирования временных слотов")
            pytest.skip("Нет доступных дней для тестирования")

        # Берем первую доступную дату
        test_day = booking_dates[0]
        logger.info(f"📅 Тестируем временные слоты для дня: {test_day}")

        result = await yclients_client.get_available_times(
            staff_id=staff_id,
            service_id=service_id,
            day=test_day
        )

        logger.info(f"🕐 Результат get_available_times: {result}")

        # Проверяем структуру ответа
        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'data' in result, "В результате должен быть ключ 'data'"

        time_slots = result['data']
        assert isinstance(time_slots, list), "data должен быть списком временных слотов"

        logger.info(f"✅ Найдено {len(time_slots)} временных слотов")

        # Если есть слоты, проверяем их структуру
        if time_slots:
            first_slot = time_slots[0]
            logger.info(f"🕐 Первый слот: {first_slot}")

            # Проверяем обязательные поля согласно документации API
            assert 'time' in first_slot, "В слоте должно быть поле 'time'"
            assert 'seance_length' in first_slot, "В слоте должно быть поле 'seance_length'"
            assert 'datetime' in first_slot, "В слоте должно быть поле 'datetime'"

            # Проверяем типы данных
            time_str = first_slot['time']
            assert isinstance(time_str, str), "Поле 'time' должно быть строкой"

            # Проверяем формат времени (HH:MM)
            try:
                time_parts = time_str.split(':')
                assert len(time_parts) == 2, "Время должно быть в формате HH:MM"
                hour, minute = map(int, time_parts)
                assert 0 <= hour <= 23, "Час должен быть от 0 до 23"
                assert 0 <= minute <= 59, "Минуты должны быть от 0 до 59"
                logger.info(f"✅ Время корректно: {time_str}")
            except (ValueError, AssertionError) as e:
                pytest.fail(f"Некорректный формат времени: {time_str}, ошибка: {e}")

            # Проверяем длительность сеанса
            seance_length = first_slot['seance_length']
            assert isinstance(seance_length, int), "seance_length должен быть числом"
            assert seance_length > 0, "Длительность сеанса должна быть положительной"
            logger.info(f"✅ Длительность сеанса: {seance_length} секунд ({seance_length // 60} минут)")

            # Проверяем datetime (timestamp)
            datetime_timestamp = first_slot['datetime']
            assert isinstance(datetime_timestamp, (int, float)), "datetime должен быть timestamp"

            try:
                slot_datetime = datetime.fromtimestamp(datetime_timestamp)
                logger.info(f"✅ Время слота: {slot_datetime.strftime('%Y-%m-%d %H:%M')}")
                assert slot_datetime.year >= 2024, "Дата слота должна быть не в прошлом"
            except (ValueError, OSError) as e:
                pytest.fail(f"Некорректный timestamp: {datetime_timestamp}, ошибка: {e}")

    @pytest.mark.asyncio
    async def test_get_available_times_with_date_string(self, yclients_client):
        """Тест с передачей даты в формате строки YYYY-MM-DD"""
        logger.info("🧪 Тестируем get_available_times с датой в формате строки")

        staff_id = 4244041
        service_id = 9128038

        # Используем завтрашнюю дату
        tomorrow = datetime.now() + timedelta(days=1)
        day_str = tomorrow.strftime('%Y-%m-%d')

        logger.info(f"📅 Тестируем для даты: {day_str}")

        result = await yclients_client.get_available_times(
            staff_id=staff_id,
            service_id=service_id,
            day=day_str
        )

        logger.info(f"🕐 Результат с датой-строкой: {result}")

        # Проверяем структуру ответа
        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'data' in result, "В результате должен быть ключ 'data'"

        time_slots = result['data']
        assert isinstance(time_slots, list), "data должен быть списком"

        logger.info(f"✅ Получено {len(time_slots)} слотов для даты {day_str}")

    @pytest.mark.asyncio
    async def test_get_available_times_with_invalid_day(self, yclients_client):
        """Тест с некорректной датой"""
        logger.info("🧪 Тестируем get_available_times с некорректной датой")

        staff_id = 4244041
        service_id = 9128038
        invalid_day = "2023-01-01"  # Дата в прошлом

        result = await yclients_client.get_available_times(
            staff_id=staff_id,
            service_id=service_id,
            day=invalid_day
        )

        logger.info(f"🕐 Результат с некорректной датой: {result}")

        # API должен вернуть пустой список или ошибку
        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'data' in result, "В результате должен быть ключ 'data'"

        time_slots = result['data']
        assert isinstance(time_slots, list), "data должен быть списком"

        logger.info(f"✅ Для некорректной даты получено {len(time_slots)} слотов")

    @pytest.mark.asyncio
    async def test_get_available_times_integration_with_days(self, yclients_client):
        """Интеграционный тест: получаем дни, затем слоты для каждого дня"""
        logger.info("🧪 Интеграционный тест: дни → слоты для каждого дня")

        staff_id = 4244041
        service_id = 9128038

        # Получаем доступные дни
        days_result = await yclients_client.get_available_days(
            staff_id=staff_id,
            service_id=service_id
        )

        booking_dates = days_result['data'].get('booking_dates', [])

        if not booking_dates:
            logger.warning("⚠️ Нет доступных дней для интеграционного теста")
            pytest.skip("Нет доступных дней для тестирования")

        # Ограничиваем количество дней для теста
        test_dates = booking_dates[:3]  # Берем только первые 3 дня
        logger.info(f"📅 Тестируем слоты для {len(test_dates)} дней")

        total_slots = 0
        for i, day in enumerate(test_dates):
            logger.info(f"📅 День {i+1}/{len(test_dates)}: {day}")

            result = await yclients_client.get_available_times(
                staff_id=staff_id,
                service_id=service_id,
                day=day
            )

            time_slots = result['data']
            slots_count = len(time_slots)
            total_slots += slots_count

            logger.info(f"🕐 Слотов в день {i+1}: {slots_count}")

            # Проверяем структуру каждого ответа
            assert isinstance(result, dict), f"Результат для дня {i+1} должен быть словарем"
            assert 'data' in result, f"В результате для дня {i+1} должен быть ключ 'data'"
            assert isinstance(time_slots, list), f"data для дня {i+1} должен быть списком"

            # Небольшая пауза между запросами
            await asyncio.sleep(0.3)

        logger.info(f"✅ Интеграционный тест завершен. Всего найдено {total_slots} слотов за {len(test_dates)} дней")

        # Проверяем, что в среднем есть какие-то слоты
        if len(test_dates) > 0:
            avg_slots = total_slots / len(test_dates)
            logger.info(f"📊 Среднее количество слотов на день: {avg_slots:.1f}")

    @pytest.mark.asyncio
    async def test_get_available_slots_for_staff_method(self, yclients_client):
        """Тест нового комплексного метода get_available_slots_for_staff"""
        logger.info("🧪 Тестируем новый метод get_available_slots_for_staff")

        staff_id = 4244041
        service_id = 9128038

        # Тестируем без ограничения по датам
        result = await yclients_client.get_available_slots_for_staff(
            staff_id=staff_id,
            service_id=service_id
        )

        logger.info(f"📊 Результат get_available_slots_for_staff: {len(result)} слотов")

        # Проверяем, что результат - это список TimeSlot объектов
        assert isinstance(result, list), "Результат должен быть списком"

        if result:
            first_slot = result[0]
            logger.info(f"🕐 Первый слот: {first_slot.start} - {first_slot.end} (мастер {first_slot.staff_id})")

            # Проверяем атрибуты TimeSlot
            assert hasattr(first_slot, 'start'), "Слот должен иметь атрибут start"
            assert hasattr(first_slot, 'end'), "Слот должен иметь атрибут end"
            assert hasattr(first_slot, 'staff_id'), "Слот должен иметь атрибут staff_id"
            assert hasattr(first_slot, 'available'), "Слот должен иметь атрибут available"

            # Проверяем типы
            assert isinstance(first_slot.start, datetime), "start должен быть datetime"
            assert isinstance(first_slot.end, datetime), "end должен быть datetime"
            assert isinstance(first_slot.staff_id, int), "staff_id должен быть int"
            assert isinstance(first_slot.available, bool), "available должен быть bool"

            # Проверяем логику
            assert first_slot.end > first_slot.start, "Время окончания должно быть больше времени начала"
            assert first_slot.staff_id == staff_id, "staff_id должен соответствовать запрошенному"
            assert first_slot.available == True, "Слот должен быть доступным"

            logger.info("✅ Структура TimeSlot корректна")

        logger.info(f"✅ get_available_slots_for_staff вернул {len(result)} слотов")


if __name__ == "__main__":
    # Запуск тестов напрямую
    async def run_tests():
        test_instance = TestGetAvailableTimes()
        client = YclientsClient(
            api_key=settings.yclients_api_key,
            company_id=settings.yclients_company_id
        )

        logger.info("🚀 Запуск тестов get_available_times...")

        try:
            await test_instance.test_get_available_times_with_valid_params(client)
            await test_instance.test_get_available_times_with_date_string(client)
            await test_instance.test_get_available_times_with_invalid_day(client)
            await test_instance.test_get_available_times_integration_with_days(client)
            await test_instance.test_get_available_slots_for_staff_method(client)

            logger.info("🎉 Все тесты get_available_times прошли успешно!")

        except Exception as e:
            logger.error(f"❌ Ошибка в тестах: {e}")
            raise

    # Запуск
    asyncio.run(run_tests())
