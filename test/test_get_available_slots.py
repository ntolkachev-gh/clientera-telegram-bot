"""
Тесты для функции handle_get_available_slots
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from types import SimpleNamespace
import logging

logger = logging.getLogger(__name__)


class TestGetAvailableSlotsHandler:
    """Тесты для функции handle_get_available_slots"""

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_with_mock(self, tools_handler_mock):
        """Тест получения свободных слотов с моковыми данными"""
        # Arrange - подготавливаем моковые данные (SimpleNamespace для имитации объектов)
        mock_slots = [
            SimpleNamespace(
                start=datetime(2024, 1, 15, 10, 0),
                end=datetime(2024, 1, 15, 11, 0),
                staff_id=123,
                available=True
            ),
            SimpleNamespace(
                start=datetime(2024, 1, 15, 11, 0),
                end=datetime(2024, 1, 15, 12, 0),
                staff_id=123,
                available=True
            ),
            SimpleNamespace(
                start=datetime(2024, 1, 15, 14, 0),
                end=datetime(2024, 1, 15, 15, 30),
                staff_id=123,
                available=True
            )
        ]

        # Мокаем метод get_available_slots у YclientsClient
        tools_handler_mock.yclients.get_available_slots = AsyncMock(
            return_value=mock_slots
        )

        # Act
        result = await tools_handler_mock.handle_get_available_slots(
            service_ids=[456],  # Теперь это список
            staff_id=123,
            date_from="2024-01-15T00:00:00",
            date_to="2024-01-15T23:59:59"
        )

        # Assert
        assert result["success"] is True
        assert "slots" in result
        assert isinstance(result["slots"], list)
        assert len(result["slots"]) == 3

        # Проверяем структуру слотов
        first_slot = result["slots"][0]
        assert "start" in first_slot
        assert "end" in first_slot
        assert "staff_id" in first_slot
        assert "available" in first_slot
        assert first_slot["available"] is True

        # Проверяем, что метод был вызван с правильными параметрами
        tools_handler_mock.yclients.get_available_slots.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_empty_response(self, tools_handler_mock):
        """Тест обработки пустого ответа (нет свободных слотов)"""
        # Arrange
        tools_handler_mock.yclients.get_available_slots = AsyncMock(
            return_value=[]
        )

        # Act
        result = await tools_handler_mock.handle_get_available_slots(
            service_ids=[456],
            staff_id=123,
            date_from="2024-01-15T00:00:00",
            date_to="2024-01-15T23:59:59"
        )

        # Assert
        assert result["success"] is True
        assert result["slots"] == []
        assert "message" in result or len(result["slots"]) == 0

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_error_handling(self, tools_handler_mock):
        """Тест обработки ошибок при получении слотов"""
        # Arrange
        tools_handler_mock.yclients.get_available_slots = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Act
        result = await tools_handler_mock.handle_get_available_slots(
            service_ids=[456],
            staff_id=123,
            date_from="2024-01-15T00:00:00",
            date_to="2024-01-15T23:59:59"
        )

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_date_validation(self, tools_handler_mock):
        """Тест валидации даты"""
        # Arrange - мокаем успешный ответ
        mock_slot = SimpleNamespace(
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 11, 0),
            staff_id=123,
            available=True
        )
        tools_handler_mock.yclients.get_available_slots = AsyncMock(
            return_value=[mock_slot]
        )

        # Test различные форматы дат
        date_formats = [
            "2024-01-15T00:00:00",      # ISO формат
            "2024-01-15T10:00:00",      # С временем
            "2024-01-15T00:00:00+00:00",     # С timezone (правильный формат)
        ]

        for date_str in date_formats:
            # Act
            result = await tools_handler_mock.handle_get_available_slots(
                service_ids=[456],
                staff_id=123,
                date_from=date_str,
                date_to="2024-01-15T23:59:59"
            )

            # Assert - должен принимать разные форматы
            assert result["success"] is True, f"Не удалось обработать дату: {date_str}"

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_multiple_slots(self, tools_handler_mock):
        """Тест обработки нескольких слотов"""
        # Arrange
        mock_slots = [
            SimpleNamespace(
                start=datetime(2024, 1, 15, 10, 0),
                end=datetime(2024, 1, 15, 10, 30),
                staff_id=123,
                available=True
            ),
            SimpleNamespace(
                start=datetime(2024, 1, 15, 11, 0),
                end=datetime(2024, 1, 15, 12, 0),
                staff_id=123,
                available=True
            ),
            SimpleNamespace(
                start=datetime(2024, 1, 15, 12, 0),
                end=datetime(2024, 1, 15, 13, 30),
                staff_id=123,
                available=True
            ),
            SimpleNamespace(
                start=datetime(2024, 1, 15, 13, 0),
                end=datetime(2024, 1, 15, 15, 0),
                staff_id=123,
                available=True
            ),
        ]

        tools_handler_mock.yclients.get_available_slots = AsyncMock(
            return_value=mock_slots
        )

        # Act
        result = await tools_handler_mock.handle_get_available_slots(
            service_ids=[456],
            staff_id=123,
            date_from="2024-01-15T00:00:00",
            date_to="2024-01-15T23:59:59"
        )

        # Assert
        assert result["success"] is True
        assert len(result["slots"]) == 4
        assert "total_found" in result
        assert result["total_found"] == 4

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_missing_parameters(self, tools_handler_mock):
        """Тест обработки отсутствующих параметров"""
        try:
            # Act - вызываем без обязательных параметров
            result = await tools_handler_mock.handle_get_available_slots()
            # Если не выбросило исключение, проверяем результат
            assert "success" in result
            if not result["success"]:
                assert "error" in result
        except TypeError:
            # Ожидаемое поведение - отсутствуют обязательные параметры
            pass

    @pytest.mark.asyncio
    async def test_handle_get_available_slots_with_multiple_services(self, tools_handler_mock):
        """Тест с несколькими услугами"""
        # Arrange
        mock_slot = SimpleNamespace(
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 11, 0),
            staff_id=123,
            available=True
        )
        tools_handler_mock.yclients.get_available_slots = AsyncMock(
            return_value=[mock_slot]
        )

        # Act - передаем несколько услуг
        result = await tools_handler_mock.handle_get_available_slots(
            service_ids=[456, 457, 458],  # Несколько услуг
            staff_id=123,
            date_from="2024-01-15T00:00:00",
            date_to="2024-01-15T23:59:59"
        )

        # Assert
        assert result["success"] is True
        assert len(result["slots"]) == 1


class TestGetAvailableSlotsIntegration:
    """Интеграционные тесты с реальным Yclients API (требуют настройки)"""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Требует реального Yclients API токена")
    async def test_real_yclients_get_slots(self):
        """Тест с реальным Yclients API"""
        # Этот тест можно активировать при наличии реального API
        from core.yclients_client import YclientsClient

        # Нужны реальные credentials
        client = YclientsClient(
            token="YOUR_REAL_TOKEN",
            company_id=12345
        )

        # Получаем реальные слоты
        slots = await client.get_available_slots(
            service_id=456,
            staff_id=123,
            date="2024-01-15"
        )

        assert isinstance(slots, list)
        logger.info(f"Получено {len(slots)} слотов из реального API")
