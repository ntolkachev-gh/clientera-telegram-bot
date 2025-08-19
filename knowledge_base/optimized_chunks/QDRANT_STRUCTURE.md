# 🗄️ Структура данных в Qdrant для LALIQ Beauty Studio

## Обзор коллекции

**Название коллекции:** `laliq_knowledge_base`
**URL Qdrant:** `http://localhost:6333`
**Размер векторов:** 384 (модель: `paraphrase-multilingual-MiniLM-L12-v2`)
**Метрика расстояния:** Cosine similarity

## Структура точки (Point) в Qdrant

Каждый чанк базы знаний представлен как точка со следующей структурой:

```json
{
  "id": "services_manicure_a1b2c3d4",
  "vector": [0.1, -0.2, 0.3, ...],  // 384-мерный вектор
  "payload": {
    // Основное содержимое
    "content": "# 💅 Маникюр и уход за руками...",

    // Базовые метаданные
    "title": "Маникюр и уход за руками - LALIQ Beauty Studio",
    "category": "services",
    "filename": "services_manicure.md",
    "language": "ru",

    // Метаданные для услуг
    "service_count": 11,
    "has_prices": true,
    "price_range": {
      "min": 390,
      "max": 3890
    },

    // Специалист (если применимо)
    "specialist": null,  // или "sevil_bammatova", "jamila_hunkaeva", "madina_bagatyrova"

    // Ключевые слова для поиска
    "keywords": ["маникюр", "ногти", "гель-лак", "наращивание", "spa"],

    // Техническая информация
    "content_length": 1723
  }
}
```

## Категории чанков

### 1. **contact_info** - Контактная информация
- **Файлы:** `contact_and_booking.md`
- **Содержит:** Телефон, процесс записи, общая статистика
- **Специальные поля:**
  - `has_prices`: false
  - `service_count`: 0

### 2. **specialists** - Специалисты
- **Файлы:** `specialists_info.md`
- **Содержит:** Информация о мастерах и их специализации
- **Специальные поля:**
  - `has_prices`: false
  - `service_count`: 0

### 3. **services** - Услуги
- **Файлы:** `services_*.md`
- **Содержит:** Описания услуг с ценами и ID
- **Специальные поля:**
  - `has_prices`: true
  - `service_count`: > 0
  - `price_range`: {min, max}
  - `specialist`: ID специалиста (если есть)

### 4. **pricing** - Ценовая информация
- **Файлы:** `pricing_overview.md`
- **Содержит:** Обзор цен по категориям
- **Специальные поля:**
  - `has_prices`: true
  - `service_count`: 78 (общее количество)

### 5. **retail** - Ритейл продукты
- **Файлы:** `retail_products.md`
- **Содержит:** Косметика и товары для продажи
- **Специальные поля:**
  - `has_prices`: false
  - `service_count`: 0

## Специалисты (Specialist IDs)

- **`sevil_bammatova`** - Brow&wax-специалист (брови, депиляция)
- **`jamila_hunkaeva`** - Lash-специалист (ресницы)
- **`madina_bagatyrova`** - Эстет-косметолог (косметология, инъекции)
- **`null`** - Общая информация или несколько специалистов

## Примеры поисковых запросов

### 1. Семантический поиск (основной)

```python
# Поиск по содержимому
query_vector = model.encode("запись к мастеру на маникюр")
search_data = {
    "vector": query_vector,
    "limit": 5,
    "with_payload": True
}
```

### 2. Поиск с фильтрацией по метаданным

```python
# Только услуги с ценами
search_data = {
    "vector": query_vector,
    "limit": 5,
    "filter": {
        "must": [
            {"key": "has_prices", "match": {"value": True}}
        ]
    },
    "with_payload": True
}

# Услуги конкретного специалиста
search_data = {
    "vector": query_vector,
    "filter": {
        "must": [
            {"key": "specialist", "match": {"value": "sevil_bammatova"}}
        ]
    },
    "with_payload": True
}

# Услуги в определенном ценовом диапазоне
search_data = {
    "vector": query_vector,
    "filter": {
        "must": [
            {"key": "price_range.min", "range": {"gte": 1000}},
            {"key": "price_range.max", "range": {"lte": 5000}}
        ]
    },
    "with_payload": True
}
```

### 3. Поиск по категориям

```python
# Только информация о специалистах
search_data = {
    "vector": query_vector,
    "filter": {
        "must": [
            {"key": "category", "match": {"value": "specialists"}}
        ]
    },
    "with_payload": True
}

# Только услуги (исключая контакты и ритейл)
search_data = {
    "vector": query_vector,
    "filter": {
        "must": [
            {"key": "category", "match": {"value": "services"}}
        ]
    },
    "with_payload": True
}
```

### 4. Комбинированные фильтры

```python
# Услуги по бровям от конкретного мастера
search_data = {
    "vector": model.encode("коррекция бровей"),
    "filter": {
        "must": [
            {"key": "category", "match": {"value": "services"}},
            {"key": "specialist", "match": {"value": "sevil_bammatova"}},
            {"key": "keywords", "match": {"any": ["брови", "коррекция"]}}
        ]
    },
    "with_payload": True
}
```

## Рекомендации по поиску

### Для чат-бота

1. **Вопросы о записи** → фильтр `category: "contact_info"`
2. **Вопросы о ценах** → фильтр `has_prices: true`
3. **Вопросы о конкретном мастере** → фильтр `specialist: "master_id"`
4. **Вопросы о конкретной услуге** → семантический поиск + фильтр `category: "services"`

### Стратегии поиска

1. **Гибридный поиск:** Комбинируйте семантический поиск с фильтрацией
2. **Fallback стратегия:** Если с фильтрами ничего не найдено, повторите без них
3. **Boost релевантность:** Для вопросов о записи повышайте релевантность `contact_info`
4. **Контекстный поиск:** Используйте `keywords` для уточнения результатов

## Примеры использования в коде

### Поиск информации для записи

```python
def search_booking_info(query: str):
    query_vector = model.encode(query)

    # Сначала ищем в контактной информации
    search_data = {
        "vector": query_vector,
        "limit": 3,
        "filter": {
            "should": [
                {"key": "category", "match": {"value": "contact_info"}},
                {"key": "category", "match": {"value": "specialists"}}
            ]
        },
        "with_payload": True
    }

    return requests.post(f"{qdrant_url}/collections/laliq_knowledge_base/points/search", json=search_data)
```

### Поиск услуг по цене

```python
def search_services_by_price(query: str, max_price: int = None):
    query_vector = model.encode(query)

    filter_conditions = [
        {"key": "category", "match": {"value": "services"}},
        {"key": "has_prices", "match": {"value": True}}
    ]

    if max_price:
        filter_conditions.append(
            {"key": "price_range.min", "range": {"lte": max_price}}
        )

    search_data = {
        "vector": query_vector,
        "limit": 5,
        "filter": {"must": filter_conditions},
        "with_payload": True
    }

    return requests.post(f"{qdrant_url}/collections/laliq_knowledge_base/points/search", json=search_data)
```

### Поиск по специалисту

```python
def search_by_specialist(query: str, specialist_name: str):
    specialist_mapping = {
        "севиль": "sevil_bammatova",
        "джамиля": "jamila_hunkaeva",
        "мадина": "madina_bagatyrova"
    }

    specialist_id = specialist_mapping.get(specialist_name.lower())
    query_vector = model.encode(query)

    search_data = {
        "vector": query_vector,
        "limit": 5,
        "filter": {
            "should": [
                {"key": "specialist", "match": {"value": specialist_id}},
                {"key": "category", "match": {"value": "specialists"}}
            ]
        },
        "with_payload": True
    }

    return requests.post(f"{qdrant_url}/collections/laliq_knowledge_base/points/search", json=search_data)
```

## Мониторинг и отладка

### Получение статистики коллекции

```bash
curl http://localhost:6333/collections/laliq_knowledge_base
```

### Просмотр всех точек

```bash
curl -X POST http://localhost:6333/collections/laliq_knowledge_base/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 100, "with_payload": true}'
```

### Удаление коллекции (для пересоздания)

```bash
curl -X DELETE http://localhost:6333/collections/laliq_knowledge_base
```

## Обновление данных

Для обновления чанков:

1. Удалите старые точки по ID
2. Загрузите новые версии
3. Или пересоздайте всю коллекцию

```python
# Удаление конкретной точки
delete_data = {"points": ["services_manicure_a1b2c3d4"]}
requests.post(f"{qdrant_url}/collections/laliq_knowledge_base/points/delete", json=delete_data)
```
