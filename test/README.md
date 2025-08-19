# 🧪 Тесты для Clientera - Laliq

## Структура тестов

```
test/
├── __init__.py                      # Инициализация пакета тестов
├── conftest.py                     # Конфигурация pytest и фикстуры
├── test_openai_tools.py            # Тесты для основных функций OpenAI Tools
├── test_get_staff.py               # Тесты для handle_get_staff
├── test_find_service_by_name.py    # Тесты для handle_find_service_by_name
├── test_find_staff_by_name.py      # Тесты для handle_find_staff_by_name
├── test_get_available_slots.py     # Тесты для handle_get_available_slots

├── test_create_booking_db.py       # Тесты для handle_create_booking с БД
├── test_embeddings_integration.py  # Интеграционные тесты для embeddings
├── requirements.txt                # Зависимости для тестов
├── run_tests.py                   # Скрипт запуска тестов
└── README.md                       # Этот файл
```

## Установка зависимостей

```bash
pip install -r test/requirements.txt
```

## 🎯 Статус тестирования

**✅ Все 61 тест проходят успешно!**
- Время выполнения: ~2.5 секунды
- Покрытие: все основные функции OpenAI Tools
- Интеграции: PostgreSQL + Qdrant + OpenAI API

## Запуск тестов

### Через скрипт run_tests.py (рекомендуется)

#### Все тесты
```bash
python test/run_tests.py
```

#### Конкретный модуль
```bash
python test/run_tests.py test/test_get_staff.py
```

#### Тесты для сервисов
```bash
python test/run_tests.py --services
```

#### Тесты для мастеров
```bash
python test/run_tests.py --staff
```

#### С покрытием кода
```bash
python test/run_tests.py --coverage
```

### Через pytest напрямую

#### Все тесты
```bash
python -m pytest test/ -v
```

#### Конкретный файл
```bash
python -m pytest test/test_get_staff.py -v
```

#### Конкретный тест
```bash
python -m pytest test/test_get_staff.py::TestGetStaffHandler::test_handle_get_staff_success -v
```

#### Несколько файлов
```bash
python -m pytest test/test_get_staff.py test/test_find_staff_by_name.py -v
```

## Тестовые фикстуры

- `real_qdrant_client` - реальный Qdrant клиент (localhost:6333)
- `real_embedding_service` - реальный EmbeddingService с Qdrant
- `mock_yclients_client` - мок YclientsClient
- `tools_handler_mock` - обработчик tools с реальным Qdrant и коллекцией laliq_knowledge_base

## Тестовые данные

### Реальный Qdrant
Тесты используют реальную базу Qdrant на `localhost:6333` с коллекцией `laliq_knowledge_base`.

### Оптимизация для экономии квоты OpenAI
- **Локальный поиск** - методы сначала пробуют искать без embeddings
- **Fallback механизм** - если локальный поиск не дает результатов, используется семантический поиск
- **Прямой доступ** - для категорий используется прямой доступ к Qdrant без векторов

### Категории данных:
- Маникюрные и педикюрные услуги
- Парикмахерские услуги (стрижки, окрашивание)
- Услуги бровей и ресниц
- Косметология и инъекции
- Информация о мастерах (specialists)

## Типы тестов

### Unit тесты
- `test_handle_get_services_success` - успешное получение услуг
- `test_handle_get_services_parsing_accuracy` - точность парсинга
- `test_handle_get_services_price_parsing` - парсинг цен
- `test_handle_get_services_qdrant_error_handling` - обработка ошибок

### Интеграционные тесты
- `test_handle_get_services_with_real_qdrant` - тест с реальным Qdrant

## Запуск через скрипт

```bash
python test/run_tests.py
```

## Отладка тестов

Для отладки конкретного теста:
```bash
python -m pytest test/test_openai_tools.py::TestGetServicesHandler::test_handle_get_services_success -v -s --pdb
```

## Маркеры тестов

- `@pytest.mark.asyncio` - асинхронные тесты
- `@pytest.mark.integration` - интеграционные тесты (требуют внешние сервисы)
