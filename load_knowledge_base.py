#!/usr/bin/env python3
"""
Скрипт для загрузки базы знаний в Qdrant Cloud
"""

import asyncio
import os
import sys

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.embedding import KnowledgeBaseManager


async def main():
    """Основная функция загрузки базы знаний"""
    print("🚀 Начинаем загрузку базы знаний в Qdrant Cloud...")
    
    try:
        # Создаем менеджер базы знаний
        kb_manager = KnowledgeBaseManager()
        
        # Загружаем базу знаний
        await kb_manager.load_knowledge_base()
        
        print("✅ База знаний успешно загружена в Qdrant Cloud!")
        
        # Тестируем поиск
        print("\n🔍 Тестируем поиск в базе знаний...")
        
        test_queries = [
            "женская стрижка",
            "окрашивание волос",
            "как записаться",
            "адрес салона",
            "стоимость услуг"
        ]
        
        for query in test_queries:
            print(f"\nПоиск: '{query}'")
            results = await kb_manager.search_knowledge_base(query, limit=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title']} (релевантность: {result['score']:.3f})")
                    print(f"     {result['content'][:100]}...")
            else:
                print("  Результаты не найдены")
        
        print("\n🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке базы знаний: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Скрипт выполнен успешно!")
        sys.exit(0)
    else:
        print("\n❌ Скрипт завершился с ошибкой!")
        sys.exit(1) 