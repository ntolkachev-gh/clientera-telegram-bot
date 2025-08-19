#!/usr/bin/env python3
"""
Интерактивный поиск по базе знаний Qdrant
"""

import requests
import json
import numpy as np
from typing import List, Dict, Optional
import sys

class KnowledgeBaseSearcher:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.qdrant_url = qdrant_url
        self.collection_name = "laliq_knowledge_base"

    def test_connection(self) -> bool:
        """Проверить подключение к Qdrant"""
        try:
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                print("✅ Подключение к Qdrant успешно!")
                return True
            else:
                print(f"❌ Ошибка подключения: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def get_collection_info(self) -> Optional[Dict]:
        """Получить информацию о коллекции"""
        try:
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Ошибка получения информации о коллекции: {e}")
            return None

    def search_by_text(self, query: str, limit: int = 5) -> Optional[Dict]:
        """Поиск по тексту в payload"""
        try:
            search_url = f"{self.qdrant_url}/collections/{self.collection_name}/points/scroll"

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
                "limit": limit,
                "with_payload": True
            }

            response = requests.post(search_url, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Ошибка поиска: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return None

    def search_by_vector(self, vector: List[float], limit: int = 5) -> Optional[Dict]:
        """Поиск по вектору"""
        try:
            search_url = f"{self.qdrant_url}/collections/{self.collection_name}/points/search"

            payload = {
                "vector": vector,
                "limit": limit,
                "with_payload": True
            }

            response = requests.post(search_url, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Ошибка поиска: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return None

    def create_random_vector(self, size: int = 1536) -> List[float]:
        """Создать случайный вектор для тестирования"""
        return np.random.rand(size).tolist()

    def print_search_results(self, query: str, results: Dict, search_type: str = "текстовый"):
        """Вывести результаты поиска"""
        if not results or 'result' not in results:
            print(f"🔍 Поиск '{query}' не дал результатов")
            return

        points = results['result'].get('points', [])
        if not points:
            print(f"🔍 Поиск '{query}' не дал результатов")
            return

        print(f"\n🔍 Результаты {search_type} поиска для: '{query}'")
        print(f"📊 Найдено документов: {len(points)}")
        print("=" * 80)

        for i, point in enumerate(points):
            print(f"\n{i+1}. 📄 Документ ID: {point['id']}")

            if 'score' in point:
                print(f"   🎯 Релевантность: {point['score']:.4f}")

            if 'payload' in point:
                payload = point['payload']

                # Заголовок
                title = payload.get('title', 'Без заголовка')
                print(f"   📝 Заголовок: {title}")

                # Файл
                file_path = payload.get('file_path', 'Неизвестный файл')
                print(f"   📁 Файл: {file_path}")

                # Контент (показываем первые 300 символов)
                content = payload.get('content', '')
                if content:
                    preview = content[:300] + "..." if len(content) > 300 else content
                    print(f"   📄 Контент: {preview}")

                # Полный текст (если есть)
                full_text = payload.get('full_text', '')
                if full_text and full_text != content:
                    print(f"   📖 Полный текст доступен (длина: {len(full_text)} символов)")

            print("-" * 80)

    def get_all_documents(self, limit: int = 10) -> Optional[Dict]:
        """Получить все документы из коллекции"""
        try:
            search_url = f"{self.qdrant_url}/collections/{self.collection_name}/points/scroll"

            payload = {
                "limit": limit,
                "with_payload": True
            }

            response = requests.post(search_url, json=payload)
            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            print(f"❌ Ошибка получения документов: {e}")
            return None

    def print_collection_stats(self):
        """Показать статистику коллекции"""
        info = self.get_collection_info()
        if info and 'result' in info:
            result = info['result']
            print("\n📊 Статистика коллекции:")
            print(f"   📁 Название: {result.get('name', 'Неизвестно')}")
            print(f"   📈 Статус: {result.get('status', 'Неизвестно')}")
            print(f"   🔢 Количество точек: {result.get('points_count', 'Неизвестно')}")

            if 'config' in result and 'params' in result['config']:
                vectors_config = result['config']['params'].get('vectors', {})
                print(f"   📏 Размер векторов: {vectors_config.get('size', 'Неизвестно')}")
                print(f"   📐 Метрика расстояния: {vectors_config.get('distance', 'Неизвестно')}")

    def interactive_search(self):
        """Интерактивный режим поиска"""
        print("🔍 Интерактивный поиск по базе знаний")
        print("=" * 50)

        if not self.test_connection():
            print("❌ Не удалось подключиться к Qdrant. Проверьте, что сервер запущен.")
            return

        self.print_collection_stats()

        print("\n📋 Доступные команды:")
        print("   /help - показать справку")
        print("   /stats - показать статистику")
        print("   /all - показать все документы")
        print("   /vector - поиск по случайному вектору")
        print("   /quit или /exit - выйти")
        print("   [текст] - поиск по тексту")
        print("-" * 50)

        while True:
            try:
                query = input("\n🔍 Введите запрос или команду: ").strip()

                if not query:
                    continue

                # Команды
                if query.lower() in ['/quit', '/exit', 'exit', 'quit']:
                    print("👋 До свидания!")
                    break

                elif query.lower() == '/help':
                    print("\n📋 Справка по командам:")
                    print("   /help - показать эту справку")
                    print("   /stats - показать статистику коллекции")
                    print("   /all - показать все документы")
                    print("   /vector - поиск по случайному вектору")
                    print("   /quit или /exit - выйти")
                    print("   [любой текст] - поиск по тексту в базе знаний")

                elif query.lower() == '/stats':
                    self.print_collection_stats()

                elif query.lower() == '/all':
                    print("\n📚 Получаем все документы...")
                    results = self.get_all_documents(limit=20)
                    if results:
                        self.print_search_results("ВСЕ ДОКУМЕНТЫ", results, "общий")
                    else:
                        print("❌ Не удалось получить документы")

                elif query.lower() == '/vector':
                    print("\n🎲 Создаем случайный вектор для поиска...")
                    vector = self.create_random_vector()
                    results = self.search_by_vector(vector)
                    if results:
                        self.print_search_results("СЛУЧАЙНЫЙ ВЕКТОР", results, "векторный")
                    else:
                        print("❌ Поиск по вектору не дал результатов")

                else:
                    # Обычный текстовый поиск
                    print(f"\n🔍 Ищем: '{query}'")
                    results = self.search_by_text(query)
                    if results:
                        self.print_search_results(query, results, "текстовый")
                    else:
                        print(f"❌ Поиск '{query}' не дал результатов")

            except KeyboardInterrupt:
                print("\n\n👋 Поиск прерван пользователем. До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")

def main():
    """Главная функция"""
    print("🚀 Запуск интерактивного поиска по базе знаний")

    # Проверяем аргументы командной строки
    qdrant_url = "http://localhost:6333"
    if len(sys.argv) > 1:
        qdrant_url = sys.argv[1]

    print(f"📍 Подключение к Qdrant: {qdrant_url}")

    # Создаем и запускаем поисковик
    searcher = KnowledgeBaseSearcher(qdrant_url)
    searcher.interactive_search()

if __name__ == "__main__":
    main()
