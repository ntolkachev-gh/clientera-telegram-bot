#!/usr/bin/env python3
"""
Быстрый поиск по базе знаний Qdrant
"""

import requests
import sys

def search_knowledge_base(query: str, qdrant_url: str = "http://localhost:6333"):
    """Быстрый поиск по базе знаний"""

    # URL для поиска
    search_url = f"{qdrant_url}/collections/knowledge_base/points/scroll"

    # Параметры поиска
    payload = {
        "filter": {
            "must": [
                {
                    "key": "content",
                    "match": {
                        "text": query
                    }
                }
            ]
        },
        "limit": 10,
        "with_payload": True
    }

    try:
        # Выполняем поиск
        response = requests.post(search_url, json=payload)

        if response.status_code == 200:
            results = response.json()

            if 'result' in results and 'points' in results['result']:
                points = results['result']['points']

                if points:
                    print(f"🔍 Найдено {len(points)} результатов для запроса: '{query}'")
                    print("=" * 80)

                    for i, point in enumerate(points):
                        print(f"\n{i+1}. 📄 Документ ID: {point['id']}")

                        if 'payload' in point:
                            payload_data = point['payload']

                            # Заголовок
                            title = payload_data.get('title', 'Без заголовка')
                            print(f"   📝 {title}")

                            # Файл
                            file_path = payload_data.get('file_path', 'Неизвестный файл')
                            print(f"   📁 {file_path}")

                            # Контент (первые 200 символов)
                            content = payload_data.get('content', '')
                            if content:
                                preview = content[:200] + "..." if len(content) > 200 else content
                                print(f"   📄 {preview}")

                            print("-" * 80)
                else:
                    print(f"🔍 Поиск '{query}' не дал результатов")
            else:
                print(f"❌ Неожиданный формат ответа")

        else:
            print(f"❌ Ошибка поиска: {response.status_code}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("🔍 Использование: python quick_search.py 'ваш запрос'")
        print("📝 Пример: python quick_search.py 'маникюр'")
        return

    # Получаем запрос из аргументов командной строки
    query = " ".join(sys.argv[1:])

    print(f"🔍 Поиск: '{query}'")
    search_knowledge_base(query)

if __name__ == "__main__":
    main()
