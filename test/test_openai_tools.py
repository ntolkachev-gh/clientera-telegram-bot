"""
Тесты для OpenAI Tools в core/openai_tools.py
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.openai_tools import YclientsToolsHandler


class TestGetServicesHandlerMock:
    """Unit тесты для функции handle_get_services с моками"""

    @pytest.mark.asyncio
    async def test_handle_get_services_success(self, tools_handler_mock):
        """Тест успешного получения услуг"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        assert result["success"] is True
        assert "services" in result
        assert "total_count" in result
        assert isinstance(result["services"], list)
        assert result["total_count"] == len(result["services"])

        # Проверяем структуру первой услуги
        if result["services"]:
            service = result["services"][0]
            required_fields = ["id", "title", "price", "price_display", "duration", "category"]
            for field in required_fields:
                assert field in service, f"Поле '{field}' отсутствует в услуге"

            # Проверяем типы данных
            assert isinstance(service["id"], int)
            assert isinstance(service["title"], str)
            assert isinstance(service["price"], int)
            assert isinstance(service["duration"], int)
            assert service["price"] > 0
            assert service["duration"] > 0

    @pytest.mark.asyncio
    async def test_handle_get_services_parsing_accuracy(self, tools_handler_mock):
        """Тест точности парсинга услуг из реальной коллекции"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        services = result["services"]
        assert len(services) > 0, "Должны быть найдены услуги в реальной коллекции"

        service_names = [s["title"] for s in services]

        # Проверяем, что есть хотя бы несколько категорий услуг
        service_text = " ".join(service_names).lower()

        # Ищем признаки различных категорий услуг
        has_beauty_services = any(keyword in service_text for keyword in
                                ["маникюр", "педикюр", "брови", "ресницы", "стрижка", "окрашивание"])

        assert has_beauty_services, f"Не найдены ожидаемые категории услуг в: {service_names[:5]}..."

    @pytest.mark.asyncio
    async def test_handle_get_services_price_parsing(self, tools_handler_mock):
        """Тест корректного парсинга цен из реальных данных"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        services = result["services"]
        assert len(services) > 0, "Должны быть найдены услуги"

        # Проверяем, что все услуги имеют корректные цены
        services_with_prices = [s for s in services if s["price"] > 0]
        assert len(services_with_prices) > 0, "Должны быть найдены услуги с ценами"

        for service in services_with_prices:
            assert service["price"] > 0, f"Некорректная цена для услуги '{service['title']}'"
            assert "₽" in service["price_display"], f"Некорректное отображение цены для '{service['title']}'"
            # Проверяем разумные ценовые диапазоны для услуг салона красоты (включая мелкие услуги как 1 капсула)
            assert 10 <= service["price"] <= 50000, f"Цена {service['price']} вне разумного диапазона для '{service['title']}'"

    @pytest.mark.asyncio
    async def test_handle_get_services_category_normalization(self, tools_handler_mock):
        """Тест нормализации категорий из реальных данных"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        services = result["services"]
        assert len(services) > 0, "Должны быть найдены услуги"

        categories = {s["category"] for s in services}
        assert len(categories) > 0, "Должны быть найдены категории услуг"

        # Проверяем, что категории содержат осмысленные названия
        category_text = " ".join(categories).lower()
        has_beauty_categories = any(keyword in category_text for keyword in
                                  ["маникюр", "парикмахер", "косметолог", "брови", "ресницы", "депиляция"])

        assert has_beauty_categories, f"Категории не содержат ожидаемых названий: {categories}"

    @pytest.mark.asyncio
    async def test_handle_get_services_duration_estimation(self, tools_handler_mock):
        """Тест оценки длительности услуг"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        services = result["services"]

        # Проверяем длительность для разных типов услуг (адаптировано под реальные данные)
        for service in services:
            title_lower = service["title"].lower()
            duration = service["duration"]

            # Проверяем базовую логику длительности - все услуги должны иметь разумную длительность
            assert 15 <= duration <= 300, f"Неразумная длительность {duration} мин для '{service['title']}'"

            # Более гибкие проверки для реальных данных
            if "наращивание" in title_lower and "1 капсула" not in title_lower:
                assert duration >= 60, f"Слишком короткая длительность для наращивания: {duration}"
            elif "маникюр" in title_lower and "снятие" not in title_lower:
                assert duration >= 30, f"Слишком короткая длительность для маникюра: {duration}"

    @pytest.mark.asyncio
    async def test_handle_get_services_no_duplicates(self, tools_handler_mock):
        """Тест отсутствия дубликатов услуг"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        services = result["services"]
        service_titles = [s["title"].lower().strip() for s in services]

        # Проверяем отсутствие дубликатов
        unique_titles = set(service_titles)
        assert len(service_titles) == len(unique_titles), \
            f"Найдены дубликаты услуг. Всего: {len(service_titles)}, уникальных: {len(unique_titles)}"

    @pytest.mark.asyncio
    async def test_handle_get_services_qdrant_error_handling(self, tools_handler_mock):
        """Тест обработки ошибок - симулируем через временную подмену клиента"""
        # Arrange - временно подменяем клиент на сломанный
        original_client = tools_handler_mock.embedding_service.qdrant_client
        from unittest.mock import Mock
        broken_client = Mock()
        broken_client.scroll.side_effect = Exception("Qdrant connection error")
        tools_handler_mock.embedding_service.qdrant_client = broken_client

        try:
            # Act
            result = await tools_handler_mock.handle_get_services()

            # Assert
            assert result["success"] is False
            assert "error" in result
            assert "Qdrant connection error" in result["error"]
        finally:
            # Restore original client
            tools_handler_mock.embedding_service.qdrant_client = original_client

    @pytest.mark.asyncio
    async def test_handle_get_services_empty_response(self, tools_handler_mock):
        """Тест обработки пустого ответа - симулируем через временную подмену клиента"""
        # Arrange - временно подменяем клиент на возвращающий пустой результат
        original_client = tools_handler_mock.embedding_service.qdrant_client
        from unittest.mock import Mock
        empty_client = Mock()
        empty_client.scroll.return_value = ([], None)
        tools_handler_mock.embedding_service.qdrant_client = empty_client

        try:
            # Act
            result = await tools_handler_mock.handle_get_services()

            # Assert
            assert result["success"] is True
            assert result["services"] == []
            assert result["total_count"] == 0
        finally:
            # Restore original client
            tools_handler_mock.embedding_service.qdrant_client = original_client

    def test_parse_services_from_content_various_formats(self, tools_handler_mock):
        """Тест парсинга различных форматов услуг"""
        # Arrange
        content = """
        # Услуги салона

        - Классический маникюр — 1200 ₽
        • Покрытие гель-лаком - 800 руб
        1. Френч — 1000 ₽
        Консультация: 500 ₽
        - Дизайн ногтей — 100-300 ₽
        """

        # Act
        services = tools_handler_mock._parse_services_from_content(
            content=content,
            category="services_manicure.md"
        )

        # Assert
        assert len(services) >= 4, f"Ожидалось минимум 4 услуги, получено: {len(services)}"

        service_names = [s["title"] for s in services]
        expected_names = ["Классический маникюр", "Покрытие гель-лаком", "Френч", "Консультация"]

        for expected in expected_names:
            assert any(expected in name for name in service_names), \
                f"Услуга '{expected}' не найдена в {service_names}"

    def test_estimate_service_duration_logic(self, tools_handler_mock):
        """Тест логики оценки длительности услуг"""
        # Test cases: (service_name, category, expected_min_duration)
        test_cases = [
            ("Наращивание ногтей", "services_manicure", 120),
            ("Ламинирование ресниц", "services_eyelashes", 120),
            ("Классический маникюр", "services_manicure", 60),
            ("Массаж лица", "services_cosmetology", 60),
            ("Ботокс", "services_injections", 45),
            ("Покрытие гель-лаком", "services_manicure", 30),
            ("Коррекция бровей", "services_eyebrows", 30),
            ("Неизвестная услуга", "unknown", 60)
        ]

        for service_name, category, expected_min_duration in test_cases:
            # Act
            duration = tools_handler_mock._estimate_service_duration(service_name, category)

            # Assert
            assert duration >= expected_min_duration, \
                f"Длительность {duration} мин для '{service_name}' меньше ожидаемой {expected_min_duration} мин"

    def test_normalize_category_name(self, tools_handler_mock):
        """Тест нормализации названий категорий"""
        test_cases = [
            ("services_manicure.md", "Маникюр"),
            ("services_hair", "Парикмахерские услуги"),
            ("services_cosmetology.md", "Косметология"),
            ("unknown_category", "Unknown Category"),
            ("path/to/services_eyebrows.md", "Брови")
        ]

        for input_category, expected_output in test_cases:
            # Act
            result = tools_handler_mock._normalize_category_name(input_category)

            # Assert
            assert result == expected_output, \
                f"Для категории '{input_category}' ожидалось '{expected_output}', получено '{result}'"


class TestGetServicesWithRealData:
    """Дополнительные тесты с реальными данными из Qdrant"""

    @pytest.mark.asyncio
    async def test_real_data_structure_validation(self, tools_handler_mock):
        """Проверка структуры реальных данных из коллекции laliq_knowledge_base"""
        # Act
        result = await tools_handler_mock.handle_get_services()

        # Assert
        assert result["success"] is True
        assert isinstance(result["services"], list)

        # Если есть услуги, проверяем их структуру
        if result["services"]:
            service = result["services"][0]
            required_fields = ["id", "title", "price", "price_display", "duration", "category"]
            for field in required_fields:
                assert field in service, f"Поле '{field}' отсутствует в структуре услуги"

            # Проверяем типы данных
            assert isinstance(service["id"], int)
            assert isinstance(service["title"], str)
            assert isinstance(service["price"], int)
            assert isinstance(service["duration"], int)
            assert isinstance(service["category"], str)
            assert isinstance(service["price_display"], str)
