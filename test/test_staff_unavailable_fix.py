"""
Тест для проверки исправления проблемы с недоступными мастерами
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from core.yclients_client import StaffUnavailableError
from core.openai_tools import YclientsToolsHandler


class TestStaffUnavailableFix:
    """Тесты для исправления проблемы недоступности мастера"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.mock_yclients = Mock()
        self.handler = YclientsToolsHandler(self.mock_yclients, telegram_id="test_user")

    @pytest.mark.asyncio
    async def test_staff_unavailable_error_handling(self):
        """Тест обработки ошибки недоступности мастера"""

        # Настраиваем мок для возврата ошибки STAFF_UNAVAILABLE
        self.mock_yclients.get_available_slots_for_staff = AsyncMock(
            side_effect=StaffUnavailableError(
                "Мастер недоступен для данной услуги",
                staff_id=3,
                service_id=4,
                error_code='STAFF_UNAVAILABLE'
            )
        )

        # Настраиваем мок для получения альтернативных мастеров
        self.handler.handle_get_staff = AsyncMock(return_value={
            'success': True,
            'staff': [
                {'id': 1, 'name': 'Мария Иванова', 'specialization': 'Маникюр'},
                {'id': 2, 'name': 'Анна Петрова', 'specialization': 'Маникюр'},
                {'id': 5, 'name': 'Елена Сидорова', 'specialization': 'Маникюр'},
            ]
        })

        # Вызываем метод с проблемными параметрами из логов
        result = await self.handler.handle_get_available_slots(
            service_ids=[4],
            date_from='2025-08-19',
            date_to='2025-09-30',
            staff_id=3
        )

        # Проверяем результат
        assert result['success'] is True
        assert result['error_code'] == 'STAFF_UNAVAILABLE'
        assert result['staff_id'] == 3
        assert result['service_id'] == 4
        assert len(result['slots']) == 0
        assert len(result['alternative_masters']) == 3
        assert result['suggestion'] == "Попробуйте выбрать другого мастера или другую услугу"

        # Проверяем, что альтернативные мастера были получены
        assert result['alternative_masters'][0]['name'] == 'Мария Иванова'
        assert result['alternative_masters'][1]['name'] == 'Анна Петрова'

        print("✅ Тест прошел успешно - ошибка STAFF_UNAVAILABLE обрабатывается корректно")

    @pytest.mark.asyncio
    async def test_no_infinite_loop(self):
        """Тест что нет бесконечного цикла при недоступности мастера"""

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                pytest.fail("Метод вызван более одного раза - возможен бесконечный цикл!")
            raise StaffUnavailableError(
                "Мастер недоступен для данной услуги",
                staff_id=3,
                service_id=4,
                error_code='STAFF_UNAVAILABLE'
            )

        self.mock_yclients.get_available_slots_for_staff = AsyncMock(side_effect=side_effect)
        self.handler.handle_get_staff = AsyncMock(return_value={'success': True, 'staff': []})

        # Вызываем метод
        result = await self.handler.handle_get_available_slots(
            service_ids=[4],
            date_from='2025-08-19',
            date_to='2025-09-30',
            staff_id=3
        )

        # Проверяем что метод вызван только один раз
        assert call_count == 1
        assert result['error_code'] == 'STAFF_UNAVAILABLE'

        print("✅ Тест прошел успешно - бесконечного цикла нет")

    @pytest.mark.asyncio
    async def test_alternative_masters_method(self):
        """Тест метода получения альтернативных мастеров"""

        # Настраиваем мок
        self.handler.handle_get_staff = AsyncMock(return_value={
            'success': True,
            'staff': [
                {'id': 1, 'name': 'Мастер 1', 'specialization': 'Маникюр'},
                {'id': 2, 'name': 'Мастер 2', 'specialization': 'Маникюр'},
                {'id': 3, 'name': 'Мастер 3', 'specialization': 'Педикюр'},
                {'id': 4, 'name': 'Мастер 4', 'specialization': 'Маникюр'},
                {'id': 5, 'name': 'Мастер 5', 'specialization': 'Маникюр'},
                {'id': 6, 'name': 'Мастер 6', 'specialization': 'Маникюр'},
            ]
        })

        # Вызываем метод
        alternatives = await self.handler._get_alternative_masters(service_id=4)

        # Проверяем результат
        assert len(alternatives) == 5  # Должно вернуть первых 5 мастеров
        assert alternatives[0]['name'] == 'Мастер 1'
        assert alternatives[4]['name'] == 'Мастер 5'

        print("✅ Тест прошел успешно - альтернативные мастера получены корректно")


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])

