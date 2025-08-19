"""
Тесты для функции handle_get_staff
"""
import pytest
from unittest.mock import Mock, AsyncMock


class TestGetStaffHandler:
    """Тесты для функции handle_get_staff с реальным Qdrant"""

    @pytest.mark.asyncio
    async def test_handle_get_staff_success(self, tools_handler_mock):
        """Тест успешного получения списка мастеров"""
        # Act
        result = await tools_handler_mock.handle_get_staff()

        # Assert
        assert result["success"] is True
        assert "staff" in result
        assert isinstance(result["staff"], list)

        # Проверяем, что есть хотя бы один мастер
        if result["staff"]:
            staff = result["staff"][0]
            # Проверяем структуру
            required_fields = ["id", "name", "specialization"]
            for field in required_fields:
                assert field in staff, f"Поле '{field}' отсутствует в структуре мастера"

            # Проверяем типы данных
            assert isinstance(staff["id"], int)
            assert isinstance(staff["name"], str)
            assert isinstance(staff["specialization"], str)

    @pytest.mark.asyncio
    async def test_handle_get_staff_known_masters(self, tools_handler_mock):
        """Тест поиска известных мастеров в результатах"""
        # Act
        result = await tools_handler_mock.handle_get_staff()

        # Assert
        assert result["success"] is True
        staff_list = result["staff"]

        # Проверяем, что найдены известные мастера
        staff_names = [s["name"] for s in staff_list]

        # Ищем хотя бы одного из известных мастеров
        known_masters = ["Севиль Бамматова", "Джамиля Хункаева", "Мадина Багатырова"]
        found_known_master = any(master in staff_names for master in known_masters)

        assert found_known_master, f"Не найден ни один из известных мастеров. Найдены: {staff_names}"

    @pytest.mark.asyncio
    async def test_handle_get_staff_specializations(self, tools_handler_mock):
        """Тест наличия специализаций у мастеров"""
        # Act
        result = await tools_handler_mock.handle_get_staff()

        # Assert
        assert result["success"] is True
        staff_list = result["staff"]

        # Проверяем, что у мастеров есть специализации
        staff_with_specialization = [s for s in staff_list if s.get("specialization") and s["specialization"] != "Специалист"]

        assert len(staff_with_specialization) > 0, "Должны быть мастера со специализацией"

        # Проверяем, что специализации содержат осмысленный текст
        for staff in staff_with_specialization:
            spec = staff["specialization"].lower()
            # Проверяем, что специализация содержит профессиональные термины
            has_prof_terms = any(term in spec for term in
                                ["brow", "lash", "мастер", "стилист", "косметолог", "массаж", "маникюр"])
            assert len(staff["specialization"]) > 5, f"Слишком короткая специализация: '{staff['specialization']}'"

    @pytest.mark.asyncio
    async def test_handle_get_staff_unique_ids(self, tools_handler_mock):
        """Тест уникальности ID мастеров"""
        # Act
        result = await tools_handler_mock.handle_get_staff()

        # Assert
        assert result["success"] is True
        staff_list = result["staff"]

        if len(staff_list) > 1:
            # Проверяем уникальность ID
            staff_ids = [s["id"] for s in staff_list]
            unique_ids = set(staff_ids)
            assert len(staff_ids) == len(unique_ids), "ID мастеров должны быть уникальными"

    @pytest.mark.asyncio
    async def test_handle_get_staff_error_handling(self, tools_handler_mock):
        """Тест обработки ошибок при получении мастеров"""
        # Arrange - временно ломаем embedding service
        original_service = tools_handler_mock.embedding_service
        broken_service = Mock()
        broken_service.search_similar = AsyncMock(side_effect=Exception("Search error"))
        tools_handler_mock.embedding_service = broken_service

        try:
            # Act
            result = await tools_handler_mock.handle_get_staff()

            # Assert
            assert result["success"] is False
            assert "error" in result
            assert "Search error" in result["error"]
        finally:
            # Restore
            tools_handler_mock.embedding_service = original_service

    @pytest.mark.asyncio
    async def test_handle_get_staff_empty_results(self, tools_handler_mock):
        """Тест обработки пустых результатов поиска"""
        # Arrange - мокаем пустой результат поиска
        original_service = tools_handler_mock.embedding_service
        mock_service = Mock()
        mock_service.search_similar = AsyncMock(return_value=[])
        tools_handler_mock.embedding_service = mock_service

        try:
            # Act
            result = await tools_handler_mock.handle_get_staff()

            # Assert
            assert result["success"] is True
            assert result["staff"] == []
        finally:
            # Restore
            tools_handler_mock.embedding_service = original_service

    @pytest.mark.asyncio
    async def test_handle_get_staff_data_consistency(self, tools_handler_mock):
        """Тест консистентности данных мастеров"""
        # Act - вызываем дважды
        result1 = await tools_handler_mock.handle_get_staff()
        result2 = await tools_handler_mock.handle_get_staff()

        # Assert - результаты должны быть консистентными
        assert result1["success"] is True
        assert result2["success"] is True

        # Количество мастеров должно быть одинаковым
        assert len(result1["staff"]) == len(result2["staff"]), "Количество мастеров должно быть консистентным"

        # Проверяем, что имена мастеров совпадают
        names1 = {s["name"] for s in result1["staff"]}
        names2 = {s["name"] for s in result2["staff"]}
        assert names1 == names2, "Списки мастеров должны быть идентичными"
