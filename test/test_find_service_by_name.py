"""
Тесты для функции handle_find_service_by_name
"""
import pytest
from unittest.mock import Mock, AsyncMock


class TestFindServiceByNameHandler:
    """Тесты для функции handle_find_service_by_name с реальным Qdrant"""

    @pytest.mark.asyncio
    async def test_find_service_by_exact_name(self, tools_handler_mock):
        """Тест поиска услуги по точному названию"""
        # Act
        result = await tools_handler_mock.handle_find_service_by_name("Маникюр")

        # Assert
        assert result["success"] is True
        assert "service" in result
        assert "found" in result

        if result["found"]:
            service = result["service"]
            assert service is not None
            assert "маникюр" in service["title"].lower()
            assert service["price"] > 0
            assert service["duration"] > 0

    @pytest.mark.asyncio
    async def test_find_service_by_partial_name(self, tools_handler_mock):
        """Тест поиска услуги по частичному названию"""
        # Act
        result = await tools_handler_mock.handle_find_service_by_name("брови")

        # Assert
        assert result["success"] is True

        if result["found"]:
            service = result["service"]
            assert "бров" in service["title"].lower()
            assert service["price"] > 0

    @pytest.mark.asyncio
    async def test_find_service_case_insensitive(self, tools_handler_mock):
        """Тест поиска услуги без учета регистра"""
        # Act
        result_lower = await tools_handler_mock.handle_find_service_by_name("маникюр")
        result_upper = await tools_handler_mock.handle_find_service_by_name("МАНИКЮР")

        # Assert
        assert result_lower["success"] is True
        assert result_upper["success"] is True

        # Результаты должны быть похожими
        if result_lower["found"] and result_upper["found"]:
            assert result_lower["service"]["title"].lower() == result_upper["service"]["title"].lower()

    @pytest.mark.asyncio
    async def test_find_nonexistent_service(self, tools_handler_mock):
        """Тест поиска несуществующей услуги"""
        # Act
        result = await tools_handler_mock.handle_find_service_by_name("НесуществующаяУслуга12345")

        # Assert
        assert result["success"] is True
        assert result["found"] is False
        assert result["service"] is None

    @pytest.mark.asyncio
    async def test_find_service_with_typo(self, tools_handler_mock):
        """Тест поиска услуги с опечаткой (нечеткий поиск)"""
        # Act
        result = await tools_handler_mock.handle_find_service_by_name("маникур")  # опечатка в "маникюр"

        # Assert
        assert result["success"] is True

        # Должен найти что-то похожее на маникюр
        if result["found"]:
            service = result["service"]
            assert "маник" in service["title"].lower()

    @pytest.mark.asyncio
    async def test_find_service_structure_validation(self, tools_handler_mock):
        """Тест проверки структуры найденной услуги"""
        # Act
        result = await tools_handler_mock.handle_find_service_by_name("педикюр")

        # Assert
        assert result["success"] is True

        if result["found"]:
            service = result["service"]
            # Проверяем обязательные поля
            required_fields = ["title", "price", "duration", "category"]
            for field in required_fields:
                assert field in service, f"Поле '{field}' отсутствует в структуре услуги"

            # Проверяем типы данных
            assert isinstance(service["title"], str)
            assert isinstance(service["price"], int)
            assert isinstance(service["duration"], int)
            assert isinstance(service["category"], str)

    @pytest.mark.asyncio
    async def test_find_service_price_validation(self, tools_handler_mock):
        """Тест валидации цены найденной услуги"""
        # Ищем несколько разных услуг
        services_to_find = ["маникюр", "стрижка", "массаж", "окрашивание"]

        for service_name in services_to_find:
            # Act
            result = await tools_handler_mock.handle_find_service_by_name(service_name)

            # Assert
            if result["found"]:
                service = result["service"]
                # Проверяем разумность цены
                assert 10 <= service["price"] <= 50000, \
                    f"Цена {service['price']} вне разумного диапазона для '{service['title']}'"
                # Проверяем разумность длительности
                assert 15 <= service["duration"] <= 300, \
                    f"Длительность {service['duration']} мин вне разумного диапазона для '{service['title']}'"

    @pytest.mark.asyncio
    async def test_find_service_error_handling(self, tools_handler_mock):
        """Тест обработки ошибок при поиске услуги"""
        # Arrange - временно ломаем embedding service
        original_service = tools_handler_mock.embedding_service
        broken_service = Mock()
        broken_service.search_similar = AsyncMock(side_effect=Exception("Search failed"))
        tools_handler_mock.embedding_service = broken_service

        try:
            # Act
            result = await tools_handler_mock.handle_find_service_by_name("маникюр")

            # Assert
            assert result["success"] is False
            assert "error" in result
            assert "Search failed" in result["error"]
        finally:
            # Restore
            tools_handler_mock.embedding_service = original_service

    @pytest.mark.asyncio
    async def test_find_service_with_special_chars(self, tools_handler_mock):
        """Тест поиска услуги со специальными символами"""
        # Act
        result = await tools_handler_mock.handle_find_service_by_name("SPA-маникюр")

        # Assert
        assert result["success"] is True

        if result["found"]:
            service = result["service"]
            # Должен найти услугу со словом SPA или маникюр
            title_lower = service["title"].lower()
            assert "spa" in title_lower or "маникюр" in title_lower

    @pytest.mark.asyncio
    async def test_find_service_consistency(self, tools_handler_mock):
        """Тест консистентности результатов поиска"""
        # Act - ищем одну и ту же услугу дважды
        result1 = await tools_handler_mock.handle_find_service_by_name("маникюр")
        result2 = await tools_handler_mock.handle_find_service_by_name("маникюр")

        # Assert
        assert result1["success"] is True
        assert result2["success"] is True

        # Результаты должны быть одинаковыми
        assert result1["found"] == result2["found"]

        if result1["found"] and result2["found"]:
            # Названия должны совпадать
            assert result1["service"]["title"] == result2["service"]["title"]
            # Цены должны совпадать
            assert result1["service"]["price"] == result2["service"]["price"]
