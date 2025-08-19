"""
Конфигурация pytest для тестов
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, MagicMock

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.openai_tools import YclientsToolsHandler
from bot.embedding import EmbeddingService
from qdrant_client.models import ScoredPoint


@pytest.fixture
def event_loop():
    """Создает новый event loop для каждого теста"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def real_qdrant_client():
    """Реальный Qdrant клиент для localhost:6333"""
    from qdrant_client import QdrantClient

    try:
        # Подключаемся к локальному Qdrant на localhost:6333
        client = QdrantClient(
            url="http://localhost:6333",
            api_key=None  # Для локального Qdrant API ключ не нужен
        )
        # Проверяем подключение
        client.get_collections()
        return client
    except Exception as e:
        pytest.skip(f"Qdrant недоступен на localhost:6333: {e}")


@pytest.fixture
def real_embedding_service(real_qdrant_client):
    """Реальный EmbeddingService с подключением к localhost:6333"""
    try:
        service = EmbeddingService()
        # Переопределяем qdrant_client для использования локального
        service.qdrant_client = real_qdrant_client
        # Переопределяем collection_name для использования правильной коллекции
        service.collection_name = "laliq_knowledge_base"

        # Проверяем, что коллекция существует
        collections = real_qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "laliq_knowledge_base" not in collection_names:
            pytest.skip("Коллекция 'laliq_knowledge_base' не найдена в Qdrant")

        return service
    except Exception as e:
        pytest.skip(f"Ошибка инициализации EmbeddingService: {e}")


@pytest.fixture
def mock_yclients_client():
    """Мок YclientsClient"""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def tools_handler_mock(mock_yclients_client, real_embedding_service):
    """Создает экземпляр YclientsToolsHandler с реальным Qdrant для всех тестов"""
    handler = YclientsToolsHandler(
        yclients_client=mock_yclients_client,
        telegram_id="test_user_123"
    )
    handler.embedding_service = real_embedding_service
    return handler


@pytest.fixture
def tools_handler_real(mock_yclients_client, real_embedding_service):
    """Создает экземпляр YclientsToolsHandler с реальным Qdrant для интеграционных тестов"""
    handler = YclientsToolsHandler(
        yclients_client=mock_yclients_client,
        telegram_id="test_user_123"
    )
    handler.embedding_service = real_embedding_service
    return handler
