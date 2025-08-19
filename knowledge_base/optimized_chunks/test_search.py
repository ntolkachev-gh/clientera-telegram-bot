#!/usr/bin/env python3
"""
Тестовый скрипт для проверки поиска в Qdrant
Запускать после загрузки данных через load_to_qdrant.py
"""

import requests
import json
from sentence_transformers import SentenceTransformer

def test_qdrant_search():
    """Тестирует различные типы поиска в Qdrant"""

    # Настройки
    qdrant_url = "http://localhost:6333"
    collection = "laliq_knowledge_base"
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    print("🧪 Тестирование поиска в Qdrant")
    print("=" * 50)

    # Проверяем подключение
    try:
        response = requests.get(f"{qdrant_url}/collections/{collection}")
        if response.status_code != 200:
            print("❌ Коллекция не найдена. Запустите сначала load_to_qdrant.py")
            return

        info = response.json()['result']
        print(f"✅ Коллекция найдена: {info['points_count']} точек")
        print()

    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        return

    # Тестовые запросы
    test_queries = [
        {
            "query": "как записаться к мастеру",
            "description": "Поиск информации о записи",
            "expected_category": "contact_info"
        },
        {
            "query": "сколько стоит маникюр",
            "description": "Поиск цен на услуги",
            "expected_category": "services"
        },
        {
            "query": "что делает Севиль Бамматова",
            "description": "Поиск по специалисту",
            "expected_specialist": "sevil_bammatova"
        },
        {
            "query": "наращивание ресниц голливуд",
            "description": "Поиск конкретной услуги",
            "expected_keywords": ["ресницы", "наращивание"]
        },
        {
            "query": "косметика для покупки",
            "description": "Поиск ритейл продуктов",
            "expected_category": "retail"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"🔍 Тест {i}: {test['description']}")
        print(f"   Запрос: '{test['query']}'")

        # Генерируем вектор
        query_vector = model.encode(test['query']).tolist()

        # Выполняем поиск
        search_data = {
            "vector": query_vector,
            "limit": 3,
            "with_payload": True,
            "score_threshold": 0.3
        }

        try:
            response = requests.post(
                f"{qdrant_url}/collections/{collection}/points/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                results = response.json()['result']

                if results:
                    best_result = results[0]
                    title = best_result['payload'].get('title', 'Без названия')
                    category = best_result['payload'].get('category', 'unknown')
                    specialist = best_result['payload'].get('specialist')
                    keywords = best_result['payload'].get('keywords', [])
                    score = best_result['score']

                    print(f"   ✅ Найдено: {title}")
                    print(f"   📊 Релевантность: {score:.3f}")
                    print(f"   🏷️  Категория: {category}")
                    if specialist:
                        print(f"   👤 Специалист: {specialist}")
                    print(f"   🔑 Ключевые слова: {', '.join(keywords[:5])}")

                    # Проверяем ожидания
                    if 'expected_category' in test and category == test['expected_category']:
                        print(f"   ✅ Категория соответствует ожиданиям")
                    elif 'expected_specialist' in test and specialist == test['expected_specialist']:
                        print(f"   ✅ Специалист соответствует ожиданиям")
                    elif 'expected_keywords' in test:
                        found_keywords = any(kw in keywords for kw in test['expected_keywords'])
                        if found_keywords:
                            print(f"   ✅ Ключевые слова найдены")
                        else:
                            print(f"   ⚠️  Ключевые слова не совпадают")

                    if score < 0.6:
                        print(f"   ⚠️  Низкая релевантность, возможно нужно улучшить запрос")

                else:
                    print("   ❌ Ничего не найдено")

            else:
                print(f"   ❌ Ошибка поиска: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

        print()

    # Тест с фильтрацией
    print("🎯 Тест фильтрации по метаданным")
    print("-" * 30)

    # Поиск только услуг с ценами
    query_vector = model.encode("процедуры салона").tolist()
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

    try:
        response = requests.post(
            f"{qdrant_url}/collections/{collection}/points/search",
            json=search_data
        )

        if response.status_code == 200:
            results = response.json()['result']
            print(f"Найдено {len(results)} услуг с ценами:")
            for result in results:
                title = result['payload'].get('title', 'Без названия')
                service_count = result['payload'].get('service_count', 0)
                price_range = result['payload'].get('price_range')
                print(f"  • {title} ({service_count} услуг)", end="")
                if price_range:
                    print(f" | {price_range['min']}-{price_range['max']} руб")
                else:
                    print()
        else:
            print(f"Ошибка фильтрации: {response.status_code}")

    except Exception as e:
        print(f"Ошибка при тестировании фильтрации: {e}")

    print()
    print("🎉 Тестирование завершено!")
    print("💡 Для более детального анализа смотрите USAGE_EXAMPLES.md")

if __name__ == "__main__":
    test_qdrant_search()
