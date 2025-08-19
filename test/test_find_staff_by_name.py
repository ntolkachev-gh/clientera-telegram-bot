"""
Тесты для функции handle_find_staff_by_name
"""
import pytest
from unittest.mock import Mock, AsyncMock


class TestFindStaffByNameHandler:
    """Тесты для функции handle_find_staff_by_name с реальным Qdrant"""

    @pytest.mark.asyncio
    async def test_find_staff_by_exact_name(self, tools_handler_mock):
        """Тест поиска мастера по точному имени"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("Севиль Бамматова")

        # Assert
        assert result["success"] is True
        assert "staff" in result
        assert "found" in result

        if result["found"]:
            staff = result["staff"]
            assert staff is not None
            assert "севиль" in staff["name"].lower()
            assert staff["id"] > 0
            assert "specialization" in staff

    @pytest.mark.asyncio
    async def test_find_staff_by_first_name_only(self, tools_handler_mock):
        """Тест поиска мастера только по имени"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("Севиль")

        # Assert
        assert result["success"] is True

        if result["found"]:
            staff = result["staff"]
            assert "севиль" in staff["name"].lower()

    @pytest.mark.asyncio
    async def test_find_staff_by_last_name_only(self, tools_handler_mock):
        """Тест поиска мастера только по фамилии"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("Бамматова")

        # Assert
        assert result["success"] is True

        if result["found"]:
            staff = result["staff"]
            assert "бамматова" in staff["name"].lower()

    @pytest.mark.asyncio
    async def test_find_staff_case_insensitive(self, tools_handler_mock):
        """Тест поиска мастера без учета регистра"""
        # Act
        result_lower = await tools_handler_mock.handle_find_staff_by_name("севиль")
        result_upper = await tools_handler_mock.handle_find_staff_by_name("СЕВИЛЬ")
        result_mixed = await tools_handler_mock.handle_find_staff_by_name("СеВиЛь")

        # Assert
        assert result_lower["success"] is True
        assert result_upper["success"] is True
        assert result_mixed["success"] is True

        # Если найдены, должны найти одного и того же мастера
        if result_lower["found"] and result_upper["found"] and result_mixed["found"]:
            name_lower = result_lower["staff"]["name"].lower()
            name_upper = result_upper["staff"]["name"].lower()
            name_mixed = result_mixed["staff"]["name"].lower()
            assert name_lower == name_upper == name_mixed

    @pytest.mark.asyncio
    async def test_find_nonexistent_staff(self, tools_handler_mock):
        """Тест поиска несуществующего мастера"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("НесуществующийМастер12345")

        # Assert
        assert result["success"] is True
        assert result["found"] is False
        assert result["staff"] is None

    @pytest.mark.asyncio
    async def test_find_staff_structure_validation(self, tools_handler_mock):
        """Тест проверки структуры найденного мастера"""
        # Ищем известных мастеров
        known_masters = ["Севиль", "Джамиля", "Мадина"]

        for master_name in known_masters:
            # Act
            result = await tools_handler_mock.handle_find_staff_by_name(master_name)

            # Assert
            if result["found"]:
                staff = result["staff"]
                # Проверяем обязательные поля
                required_fields = ["id", "name", "specialization"]
                for field in required_fields:
                    assert field in staff, f"Поле '{field}' отсутствует в структуре мастера"

                # Проверяем типы данных
                assert isinstance(staff["id"], int)
                assert isinstance(staff["name"], str)
                assert isinstance(staff["specialization"], str)

    @pytest.mark.asyncio
    async def test_find_staff_specialization_present(self, tools_handler_mock):
        """Тест наличия специализации у найденного мастера"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("Севиль Бамматова")

        # Assert
        assert result["success"] is True

        if result["found"]:
            staff = result["staff"]
            assert "specialization" in staff
            assert len(staff["specialization"]) > 0
            # Специализация должна содержать осмысленный текст
            spec_lower = staff["specialization"].lower()
            has_prof_terms = any(term in spec_lower for term in
                                ["brow", "lash", "мастер", "стилист", "косметолог", "универсальный"])
            assert has_prof_terms or staff["specialization"] == "Универсальный мастер"

    @pytest.mark.asyncio
    async def test_find_staff_id_stability(self, tools_handler_mock):
        """Тест стабильности ID мастера"""
        # Act - ищем одного мастера несколько раз
        result1 = await tools_handler_mock.handle_find_staff_by_name("Севиль Бамматова")
        result2 = await tools_handler_mock.handle_find_staff_by_name("Севиль Бамматова")

        # Assert
        if result1["found"] and result2["found"]:
            # ID должен быть одинаковым для одного и того же мастера
            assert result1["staff"]["id"] == result2["staff"]["id"]

    @pytest.mark.asyncio
    async def test_find_staff_with_typo(self, tools_handler_mock):
        """Тест поиска мастера с опечаткой"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("Севил")  # без мягкого знака

        # Assert
        assert result["success"] is True

        # Может найти похожего мастера
        if result["found"]:
            staff = result["staff"]
            assert "севи" in staff["name"].lower()

    @pytest.mark.asyncio
    async def test_find_staff_error_handling(self, tools_handler_mock):
        """Тест обработки ошибок при поиске мастера"""
        # Arrange - временно ломаем embedding service
        original_service = tools_handler_mock.embedding_service
        broken_service = Mock()
        broken_service.search_similar = AsyncMock(side_effect=Exception("Search error"))
        tools_handler_mock.embedding_service = broken_service

        try:
            # Act
            result = await tools_handler_mock.handle_find_staff_by_name("Севиль")

            # Assert
            assert result["success"] is False
            assert "error" in result
            assert "Search error" in result["error"]
        finally:
            # Restore
            tools_handler_mock.embedding_service = original_service

    @pytest.mark.asyncio
    async def test_find_staff_empty_name(self, tools_handler_mock):
        """Тест поиска с пустым именем"""
        # Act
        result = await tools_handler_mock.handle_find_staff_by_name("")

        # Assert
        assert result["success"] is True
        # С пустым именем не должен найти конкретного мастера
        assert result["found"] is False

    @pytest.mark.asyncio
    async def test_find_staff_consistency(self, tools_handler_mock):
        """Тест консистентности результатов поиска мастера"""
        # Act - ищем одного мастера дважды
        result1 = await tools_handler_mock.handle_find_staff_by_name("Джамиля")
        result2 = await tools_handler_mock.handle_find_staff_by_name("Джамиля")

        # Assert
        assert result1["success"] is True
        assert result2["success"] is True

        # Результаты должны быть одинаковыми
        assert result1["found"] == result2["found"]

        if result1["found"] and result2["found"]:
            # Данные должны совпадать
            assert result1["staff"]["name"] == result2["staff"]["name"]
            assert result1["staff"]["id"] == result2["staff"]["id"]
            assert result1["staff"]["specialization"] == result2["staff"]["specialization"]
