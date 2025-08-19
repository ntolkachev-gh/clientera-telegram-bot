"""
Интеграционные тесты для новых методов поиска доступных слотов YClients API
"""
import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from core.yclients_client import YclientsClient
from core.openai_tools import YclientsToolsHandler
from config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAvailableSlotsIntegration:
    """Интеграционные тесты для методов поиска слотов"""

    @pytest.fixture
    def yclients_client(self):
        """Создание клиента YClients для тестов"""
        return YclientsClient(
            api_key=settings.yclients_api_key,
            company_id=settings.yclients_company_id
        )

    @pytest.fixture
    def tools_handler(self, yclients_client):
        """Создание обработчика tools для тестов"""
        return YclientsToolsHandler(yclients_client)

    @pytest.mark.asyncio
    async def test_new_vs_old_methods_comparison(self, yclients_client):
        """Сравнение результатов новых и старых методов"""
        logger.info("🧪 Сравниваем новые и старые методы поиска слотов")

        staff_id = 4244041
        service_id = 9128038
        date_from = datetime.now()
        date_to = datetime.now() + timedelta(days=7)

        logger.info(f"📅 Период поиска: {date_from.strftime('%Y-%m-%d')} - {date_to.strftime('%Y-%m-%d')}")

        # Новый метод
        logger.info("🆕 Тестируем новый метод get_available_slots_for_staff")
        new_slots = await yclients_client.get_available_slots_for_staff(
            staff_id=staff_id,
            service_id=service_id,
            date_from=date_from,
            date_to=date_to
        )

        # Старый метод
        logger.info("🔄 Тестируем старый метод get_available_slots")
        old_slots = await yclients_client.get_available_slots(
            service_ids=[service_id],
            date_from=date_from,
            date_to=date_to,
            staff_id=staff_id,
            use_real_api=True
        )

        logger.info(f"📊 Новый метод: {len(new_slots)} слотов")
        logger.info(f"📊 Старый метод: {len(old_slots)} слотов")

        # Оба метода должны возвращать списки TimeSlot
        assert isinstance(new_slots, list), "Новый метод должен возвращать список"
        assert isinstance(old_slots, list), "Старый метод должен возвращать список"

        # Если есть результаты, сравниваем структуру
        if new_slots and old_slots:
            new_slot = new_slots[0]
            old_slot = old_slots[0]

            # Проверяем, что оба возвращают объекты одного типа
            assert type(new_slot) == type(old_slot), "Оба метода должны возвращать объекты одного типа"
            assert hasattr(new_slot, 'start'), "Слоты должны иметь атрибут start"
            assert hasattr(new_slot, 'staff_id'), "Слоты должны иметь атрибут staff_id"

            logger.info("✅ Структуры слотов совместимы")

        logger.info("✅ Сравнение методов завершено")

    @pytest.mark.asyncio
    async def test_tools_handler_new_methods(self, tools_handler):
        """Тест новых методов через tools handler"""
        logger.info("🧪 Тестируем новые методы через tools handler")

        staff_id = 4244041
        service_id = 9128038

        # Тестируем handle_get_available_days
        logger.info("📅 Тестируем handle_get_available_days")
        days_result = await tools_handler.handle_get_available_days(
            staff_id=staff_id,
            service_id=service_id
        )

        logger.info(f"📊 Результат handle_get_available_days: {days_result}")

        assert isinstance(days_result, dict), "Результат должен быть словарем"
        assert 'success' in days_result, "В результате должен быть ключ success"
        assert days_result['success'] == True, "Вызов должен быть успешным"
        assert 'days' in days_result, "В результате должен быть ключ days"
        assert 'total_found' in days_result, "В результате должен быть ключ total_found"

        days = days_result['days']
        assert isinstance(days, list), "days должен быть списком"

        logger.info(f"✅ handle_get_available_days вернул {len(days)} дней")

        # Если есть доступные дни, тестируем handle_get_available_times
        if days and days_result['total_found'] > 0:
            first_day = days[0]
            test_day = first_day.get('date') or first_day.get('timestamp')

            if test_day:
                logger.info(f"🕐 Тестируем handle_get_available_times для дня: {test_day}")
                times_result = await tools_handler.handle_get_available_times(
                    staff_id=staff_id,
                    service_id=service_id,
                    day=str(test_day)
                )

                logger.info(f"📊 Результат handle_get_available_times: {times_result}")

                assert isinstance(times_result, dict), "Результат должен быть словарем"
                assert 'success' in times_result, "В результате должен быть ключ success"
                assert times_result['success'] == True, "Вызов должен быть успешным"
                assert 'slots' in times_result, "В результате должен быть ключ slots"
                assert 'total_found' in times_result, "В результате должен быть ключ total_found"

                slots = times_result['slots']
                assert isinstance(slots, list), "slots должен быть списком"

                logger.info(f"✅ handle_get_available_times вернул {len(slots)} слотов")

                # Проверяем структуру форматированных слотов
                if slots:
                    first_slot = slots[0]
                    assert 'time' in first_slot, "В слоте должно быть поле time"
                    assert 'duration_minutes' in first_slot, "В слоте должно быть поле duration_minutes"
                    assert 'start_datetime' in first_slot or 'datetime' in first_slot, "В слоте должно быть время"

                    logger.info(f"🕐 Первый слот: {first_slot['time']} ({first_slot['duration_minutes']} мин)")

    @pytest.mark.asyncio
    async def test_enhanced_get_available_slots_with_staff(self, tools_handler):
        """Тест улучшенного метода get_available_slots с использованием новых методов"""
        logger.info("🧪 Тестируем улучшенный get_available_slots с конкретным мастером")

        staff_id = 4244041
        service_id = 9128038
        date_from = datetime.now().strftime('%Y-%m-%d')
        date_to = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')

        # Тестируем с одной услугой и конкретным мастером (должен использовать новые методы)
        result = await tools_handler.handle_get_available_slots(
            service_ids=[service_id],
            date_from=date_from,
            date_to=date_to,
            staff_id=staff_id
        )

        logger.info(f"📊 Результат улучшенного get_available_slots: {result}")

        assert isinstance(result, dict), "Результат должен быть словарем"
        assert 'success' in result, "В результате должен быть ключ success"
        assert 'slots' in result, "В результате должен быть ключ slots"
        assert 'total_found' in result, "В результате должен быть ключ total_found"

        if result['success']:
            slots = result['slots']
            assert isinstance(slots, list), "slots должен быть списком"

            logger.info(f"✅ Найдено {result['total_found']} слотов (показано {len(slots)})")

            # Проверяем структуру слотов
            if slots:
                first_slot = slots[0]
                assert 'start' in first_slot, "В слоте должно быть поле start"
                assert 'end' in first_slot, "В слоте должно быть поле end"
                assert 'staff_id' in first_slot, "В слоте должно быть поле staff_id"
                assert 'available' in first_slot, "В слоте должно быть поле available"

                assert first_slot['staff_id'] == staff_id, "staff_id должен соответствовать запрошенному"
                logger.info(f"🕐 Первый слот: {first_slot['start']} - {first_slot['end']}")
        else:
            logger.warning(f"⚠️ Вызов завершился с ошибкой: {result.get('error', 'Неизвестная ошибка')}")

    @pytest.mark.asyncio
    async def test_error_handling(self, tools_handler):
        """Тест обработки ошибок в новых методах"""
        logger.info("🧪 Тестируем обработку ошибок в новых методах")

        # Тест с несуществующими ID
        invalid_staff_id = 999999999
        invalid_service_id = 999999999

        # Тестируем handle_get_available_days с некорректными параметрами
        logger.info("📅 Тестируем get_available_days с некорректными ID")
        days_result = await tools_handler.handle_get_available_days(
            staff_id=invalid_staff_id,
            service_id=invalid_service_id
        )

        logger.info(f"📊 Результат с некорректными ID: {days_result}")

        # Метод должен вернуть результат (возможно пустой), но не упасть с ошибкой
        assert isinstance(days_result, dict), "Результат должен быть словарем"
        assert 'success' in days_result, "В результате должен быть ключ success"

        # Тестируем handle_get_available_times с некорректной датой
        logger.info("🕐 Тестируем get_available_times с некорректной датой")
        times_result = await tools_handler.handle_get_available_times(
            staff_id=4244041,
            service_id=9128038,
            day="invalid-date"
        )

        logger.info(f"📊 Результат с некорректной датой: {times_result}")

        assert isinstance(times_result, dict), "Результат должен быть словарем"
        assert 'success' in times_result, "В результате должен быть ключ success"

        logger.info("✅ Обработка ошибок работает корректно")

    @pytest.mark.asyncio
    async def test_performance_comparison(self, yclients_client):
        """Сравнение производительности новых и старых методов"""
        logger.info("🧪 Сравниваем производительность новых и старых методов")

        staff_id = 4244041
        service_id = 9128038
        date_from = datetime.now()
        date_to = datetime.now() + timedelta(days=2)

        # Тестируем новый метод
        start_time = datetime.now()
        new_slots = await yclients_client.get_available_slots_for_staff(
            staff_id=staff_id,
            service_id=service_id,
            date_from=date_from,
            date_to=date_to
        )
        new_method_time = (datetime.now() - start_time).total_seconds()

        # Небольшая пауза между тестами
        await asyncio.sleep(1)

        # Тестируем старый метод
        start_time = datetime.now()
        old_slots = await yclients_client.get_available_slots(
            service_ids=[service_id],
            date_from=date_from,
            date_to=date_to,
            staff_id=staff_id,
            use_real_api=True
        )
        old_method_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"⏱️ Новый метод: {new_method_time:.2f} сек ({len(new_slots)} слотов)")
        logger.info(f"⏱️ Старый метод: {old_method_time:.2f} сек ({len(old_slots)} слотов)")

        # Оба метода должны работать в разумное время (меньше 30 секунд)
        assert new_method_time < 30, f"Новый метод слишком медленный: {new_method_time:.2f} сек"
        assert old_method_time < 30, f"Старый метод слишком медленный: {old_method_time:.2f} сек"

        logger.info("✅ Тест производительности завершен")


if __name__ == "__main__":
    # Запуск тестов напрямую
    async def run_tests():
        test_instance = TestAvailableSlotsIntegration()
        client = YclientsClient(
            api_key=settings.yclients_api_key,
            company_id=settings.yclients_company_id
        )
        handler = YclientsToolsHandler(client)

        logger.info("🚀 Запуск интеграционных тестов...")

        try:
            await test_instance.test_new_vs_old_methods_comparison(client)
            await test_instance.test_tools_handler_new_methods(handler)
            await test_instance.test_enhanced_get_available_slots_with_staff(handler)
            await test_instance.test_error_handling(handler)
            await test_instance.test_performance_comparison(client)

            logger.info("🎉 Все интеграционные тесты прошли успешно!")

        except Exception as e:
            logger.error(f"❌ Ошибка в тестах: {e}")
            raise

    # Запуск
    asyncio.run(run_tests())
