# 🔍 Примеры использования поиска в Qdrant

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск Qdrant (Docker)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Загрузка данных

```bash
python load_to_qdrant.py
```

## Примеры поисковых запросов для чат-бота

### Базовый поиск

```python
from sentence_transformers import SentenceTransformer
import requests

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
qdrant_url = "http://localhost:6333"
collection = "laliq_knowledge_base"

def search_knowledge_base(query: str, limit: int = 3):
    """Базовый семантический поиск"""
    query_vector = model.encode(query).tolist()

    search_data = {
        "vector": query_vector,
        "limit": limit,
        "with_payload": True,
        "score_threshold": 0.5  # Минимальная релевантность
    }

    response = requests.post(
        f"{qdrant_url}/collections/{collection}/points/search",
        json=search_data
    )

    return response.json()['result'] if response.status_code == 200 else []
```

### Специализированные поисковые функции

#### 1. Поиск информации для записи

```python
def search_booking_info(query: str):
    """Поиск информации о записи, контактах, специалистах"""
    query_vector = model.encode(query).tolist()

    search_data = {
        "vector": query_vector,
        "limit": 5,
        "filter": {
            "should": [
                {"key": "category", "match": {"value": "contact_info"}},
                {"key": "category", "match": {"value": "specialists"}}
            ]
        },
        "with_payload": True
    }

    response = requests.post(f"{qdrant_url}/collections/{collection}/points/search", json=search_data)
    return response.json()['result'] if response.status_code == 200 else []

# Примеры запросов:
results = search_booking_info("как записаться к мастеру")
results = search_booking_info("телефон для записи")
results = search_booking_info("кто работает в салоне")
```

#### 2. Поиск услуг с фильтрацией по цене

```python
def search_services_by_price(query: str, max_price: int = None, min_price: int = None):
    """Поиск услуг в определенном ценовом диапазоне"""
    query_vector = model.encode(query).tolist()

    filter_conditions = [
        {"key": "category", "match": {"value": "services"}},
        {"key": "has_prices", "match": {"value": True}}
    ]

    if max_price:
        filter_conditions.append({"key": "price_range.max", "range": {"lte": max_price}})
    if min_price:
        filter_conditions.append({"key": "price_range.min", "range": {"gte": min_price}})

    search_data = {
        "vector": query_vector,
        "limit": 10,
        "filter": {"must": filter_conditions},
        "with_payload": True
    }

    response = requests.post(f"{qdrant_url}/collections/{collection}/points/search", json=search_data)
    return response.json()['result'] if response.status_code == 200 else []

# Примеры запросов:
results = search_services_by_price("маникюр", max_price=2000)
results = search_services_by_price("дорогие процедуры", min_price=5000)
results = search_services_by_price("средние цены", min_price=1000, max_price=3000)
```

#### 3. Поиск по конкретному специалисту

```python
def search_by_specialist(query: str, specialist_name: str = None):
    """Поиск услуг конкретного специалиста"""
    specialist_mapping = {
        "севиль": "sevil_bammatova",
        "бамматова": "sevil_bammatova",
        "джамиля": "jamila_hunkaeva",
        "хункаева": "jamila_hunkaeva",
        "мадина": "madina_bagatyrova",
        "багатырова": "madina_bagatyrova"
    }

    query_vector = model.encode(query).tolist()

    if specialist_name:
        specialist_id = specialist_mapping.get(specialist_name.lower())
        if specialist_id:
            filter_condition = {
                "should": [
                    {"key": "specialist", "match": {"value": specialist_id}},
                    {"key": "category", "match": {"value": "specialists"}}
                ]
            }
        else:
            # Если специалист не найден, ищем в общей информации о специалистах
            filter_condition = {"key": "category", "match": {"value": "specialists"}}
    else:
        # Поиск среди всех специалистов
        filter_condition = {
            "should": [
                {"key": "category", "match": {"value": "specialists"}},
                {"key": "specialist", "match": {"any": ["sevil_bammatova", "jamila_hunkaeva", "madina_bagatyrova"]}}
            ]
        }

    search_data = {
        "vector": query_vector,
        "limit": 5,
        "filter": filter_condition,
        "with_payload": True
    }

    response = requests.post(f"{qdrant_url}/collections/{collection}/points/search", json=search_data)
    return response.json()['result'] if response.status_code == 200 else []

# Примеры запросов:
results = search_by_specialist("брови", "севиль")
results = search_by_specialist("ресницы", "джамиля")
results = search_by_specialist("кто делает косметологию", "мадина")
```

#### 4. Поиск по ключевым словам

```python
def search_by_keywords(query: str, keywords: list):
    """Поиск с дополнительной фильтрацией по ключевым словам"""
    query_vector = model.encode(query).tolist()

    search_data = {
        "vector": query_vector,
        "limit": 5,
        "filter": {
            "must": [
                {"key": "keywords", "match": {"any": keywords}}
            ]
        },
        "with_payload": True
    }

    response = requests.post(f"{qdrant_url}/collections/{collection}/points/search", json=search_data)
    return response.json()['result'] if response.status_code == 200 else []

# Примеры запросов:
results = search_by_keywords("процедуры для лица", ["косметология", "пилинг", "чистка"])
results = search_by_keywords("уход за ногтями", ["маникюр", "ногти", "гель-лак"])
```

### Комплексная поисковая функция для чат-бота

```python
def smart_search(query: str, context: dict = None):
    """
    Умный поиск с контекстом и fallback стратегией

    Args:
        query: Поисковый запрос пользователя
        context: Контекст разговора (специалист, категория услуг и т.д.)
    """

    # Определяем тип запроса
    query_lower = query.lower()

    # 1. Вопросы о записи
    if any(word in query_lower for word in ['запись', 'записаться', 'телефон', 'номер', 'контакт']):
        results = search_booking_info(query)
        if results:
            return {"type": "booking", "results": results}

    # 2. Вопросы о ценах
    if any(word in query_lower for word in ['цена', 'стоимость', 'сколько', 'прайс']):
        # Сначала ищем конкретные услуги с ценами
        results = search_services_by_price(query)
        if not results:
            # Если не найдено, ищем общую ценовую информацию
            results = search_knowledge_base(query + " цены прайс")
        if results:
            return {"type": "pricing", "results": results}

    # 3. Вопросы о специалистах
    specialist_names = ['севиль', 'джамиля', 'мадина', 'бамматова', 'хункаева', 'багатырова']
    mentioned_specialist = None
    for name in specialist_names:
        if name in query_lower:
            mentioned_specialist = name
            break

    if mentioned_specialist or any(word in query_lower for word in ['мастер', 'специалист', 'кто']):
        results = search_by_specialist(query, mentioned_specialist)
        if results:
            return {"type": "specialist", "results": results}

    # 4. Вопросы об услугах
    if any(word in query_lower for word in ['услуг', 'процедур', 'делаете', 'есть ли']):
        results = search_knowledge_base(query)
        # Фильтруем только услуги
        service_results = [r for r in results if r.get('payload', {}).get('category') == 'services']
        if service_results:
            return {"type": "services", "results": service_results}

    # 5. Общий поиск как fallback
    results = search_knowledge_base(query)
    return {"type": "general", "results": results}

# Пример использования:
def chatbot_response(user_query: str):
    """Функция для получения ответа чат-бота"""
    search_result = smart_search(user_query)

    if not search_result["results"]:
        return "Извините, я не нашел информацию по вашему запросу. Позвоните нам по телефону +7 988 264-73-44"

    # Берем самый релевантный результат
    best_result = search_result["results"][0]
    content = best_result["payload"]["content"]
    score = best_result["score"]

    # Если релевантность низкая, предлагаем связаться с администратором
    if score < 0.6:
        return f"Вот что я нашел:\n\n{content[:500]}...\n\nДля более точной информации рекомендую позвонить +7 988 264-73-44"

    return content
```

### Примеры запросов и ожидаемых результатов

```python
# Тестирование различных запросов
test_queries = [
    "как записаться на маникюр",           # -> booking info
    "сколько стоит наращивание ресниц",    # -> services with prices
    "что делает Севиль",                   # -> specialist info
    "какие есть процедуры для лица",       # -> cosmetology services
    "дорогие услуги в салоне",             # -> pricing overview
    "что можно купить в салоне",           # -> retail products
    "телефон салона",                      # -> contact info
    "кто работает с бровями"               # -> specialist search
]

for query in test_queries:
    print(f"\n🔍 Запрос: {query}")
    result = smart_search(query)
    print(f"📊 Тип: {result['type']}")
    if result['results']:
        best = result['results'][0]
        print(f"📄 Найдено: {best['payload']['title']}")
        print(f"⭐ Релевантность: {best['score']:.3f}")
    else:
        print("❌ Ничего не найдено")
```

### Интеграция с веб-приложением

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def api_search():
    """API endpoint для поиска"""
    data = request.json
    query = data.get('query', '')

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        result = smart_search(query)
        return jsonify({
            "query": query,
            "type": result["type"],
            "results": result["results"][:3],  # Ограничиваем до 3 результатов
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/chatbot', methods=['POST'])
def chatbot_endpoint():
    """Endpoint для чат-бота"""
    data = request.json
    query = data.get('message', '')

    if not query:
        return jsonify({"error": "Message is required"}), 400

    try:
        response = chatbot_response(query)
        return jsonify({
            "message": query,
            "response": response,
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

Теперь у вас есть полнофункциональная система поиска в базе знаний с различными стратегиями и примерами использования!
