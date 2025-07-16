import os
import re
import markdown
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from bot.openai_client import OpenAIClient
from config import settings
from database.database import SessionLocal


class KnowledgeBaseManager:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.collection_name = "knowledge_base"
        self.knowledge_base_path = "./knowledge_base"
        
    async def init_collection(self):
        """Инициализация коллекции в Qdrant"""
        try:
            # Проверяем, существует ли коллекция
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if not collection_exists:
                # Создаем коллекцию
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # Размер эмбеддингов text-embedding-3-small
                        distance=Distance.COSINE
                    )
                )
                print(f"Коллекция {self.collection_name} создана")
            else:
                print(f"Коллекция {self.collection_name} уже существует")
                
        except Exception as e:
            print(f"Ошибка при инициализации коллекции: {e}")

    def parse_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Парсинг Markdown файла на чанки по заголовкам ##"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Разделяем по заголовкам ##
            sections = re.split(r'\n## ', content)
            chunks = []
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                
                # Добавляем ## обратно (кроме первой секции)
                if i > 0:
                    section = "## " + section
                
                # Извлекаем заголовок
                lines = section.split('\n')
                title = lines[0].strip().replace('##', '').strip()
                
                # Получаем содержимое
                content_lines = lines[1:] if len(lines) > 1 else []
                content_text = '\n'.join(content_lines).strip()
                
                if content_text:
                    chunks.append({
                        "title": title,
                        "content": content_text,
                        "file_path": file_path,
                        "full_text": section
                    })
            
            return chunks
            
        except Exception as e:
            print(f"Ошибка при парсинге файла {file_path}: {e}")
            return []

    def get_all_markdown_files(self) -> List[str]:
        """Получение всех Markdown файлов из папки knowledge_base"""
        md_files = []
        
        if not os.path.exists(self.knowledge_base_path):
            os.makedirs(self.knowledge_base_path)
            print(f"Создана папка {self.knowledge_base_path}")
            return md_files
        
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
        
        return md_files

    async def load_knowledge_base(self):
        """Загрузка всей базы знаний в Qdrant"""
        print("Начинаем загрузку базы знаний...")
        
        # Инициализируем коллекцию
        await self.init_collection()
        
        # Очищаем коллекцию
        self.qdrant_client.delete_collection(self.collection_name)
        await self.init_collection()
        
        # Получаем все файлы
        md_files = self.get_all_markdown_files()
        
        if not md_files:
            print("Markdown файлы не найдены в папке knowledge_base")
            return
        
        # Парсим все файлы
        all_chunks = []
        for file_path in md_files:
            chunks = self.parse_markdown_file(file_path)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            print("Не найдено содержимого для загрузки")
            return
        
        print(f"Найдено {len(all_chunks)} чанков для загрузки")
        
        # Создаем эмбеддинги
        with SessionLocal() as db:
            openai_client = OpenAIClient(db)
            
            # Подготавливаем тексты для эмбеддингов
            texts = [f"{chunk['title']}\n\n{chunk['content']}" for chunk in all_chunks]
            
            # Создаем эмбеддинги батчами
            batch_size = 100
            points = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_chunks = all_chunks[i:i + batch_size]
                
                embeddings = await openai_client.create_embeddings(batch_texts)
                
                for j, embedding in enumerate(embeddings):
                    chunk_idx = i + j
                    point = PointStruct(
                        id=chunk_idx,
                        vector=embedding,
                        payload={
                            "title": batch_chunks[j]["title"],
                            "content": batch_chunks[j]["content"],
                            "file_path": batch_chunks[j]["file_path"],
                            "full_text": batch_chunks[j]["full_text"]
                        }
                    )
                    points.append(point)
                
                print(f"Обработано {min(i + batch_size, len(texts))} из {len(texts)} чанков")
            
            # Загружаем в Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"Загружено {len(points)} чанков в Qdrant")

    async def search_knowledge_base(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск в базе знаний по запросу"""
        try:
            # Создаем эмбеддинг для запроса
            with SessionLocal() as db:
                openai_client = OpenAIClient(db)
                query_embeddings = await openai_client.create_embeddings([query])
                
                if not query_embeddings:
                    return []
                
                query_embedding = query_embeddings[0]
            
            # Поиск в Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            results = []
            for result in search_results:
                results.append({
                    "title": result.payload["title"],
                    "content": result.payload["content"],
                    "file_path": result.payload["file_path"],
                    "score": result.score
                })
            
            return results
            
        except Exception as e:
            print(f"Ошибка при поиске в базе знаний: {e}")
            return []

    async def answer_question(self, question: str) -> str:
        """Ответ на вопрос с использованием базы знаний"""
        # Ищем релевантную информацию
        search_results = await self.search_knowledge_base(question, limit=3)
        
        if not search_results:
            return "Извините, я не нашел информации по вашему вопросу в базе знаний."
        
        # Формируем контекст
        context = "\n\n".join([
            f"**{result['title']}**\n{result['content']}"
            for result in search_results
        ])
        
        # Генерируем ответ с помощью GPT
        with SessionLocal() as db:
            openai_client = OpenAIClient(db)
            
            messages = [
                {
                    "role": "system",
                    "content": """Ты - помощник в салоне красоты. 
                    Отвечай на вопросы клиентов, используя только предоставленную информацию из базы знаний.
                    Если информации недостаточно, честно скажи об этом.
                    Отвечай дружелюбно и профессионально."""
                },
                {
                    "role": "user",
                    "content": f"""Вопрос клиента: {question}
                    
                    Информация из базы знаний:
                    {context}
                    
                    Ответь на вопрос, используя эту информацию."""
                }
            ]
            
            response = await openai_client.chat_completion(messages)
            return response

    def create_sample_knowledge_base(self):
        """Создание примера базы знаний"""
        if not os.path.exists(self.knowledge_base_path):
            os.makedirs(self.knowledge_base_path)
        
        sample_content = """# Информация о салоне красоты

## Услуги

### Маникюр
- Классический маникюр - 1500 руб., 60 мин
- Аппаратный маникюр - 1800 руб., 45 мин
- Покрытие гель-лаком - 800 руб., 30 мин

### Педикюр
- Классический педикюр - 2000 руб., 90 мин
- Аппаратный педикюр - 2200 руб., 75 мин

### Брови
- Коррекция бровей - 800 руб., 30 мин
- Окрашивание бровей - 600 руб., 20 мин
- Ламинирование бровей - 2500 руб., 60 мин

## Мастера

### Наталья Иванова
Специализация: маникюр, педикюр
Опыт работы: 5 лет
Работает: Пн-Пт 10:00-19:00

### Елена Петрова
Специализация: брови, ресницы
Опыт работы: 3 года
Работает: Вт-Сб 11:00-20:00

## Режим работы

Понедельник-Пятница: 10:00-20:00
Суббота: 10:00-18:00
Воскресенье: выходной

## Контакты

Адрес: г. Москва, ул. Примерная, д. 1
Телефон: +7 (495) 123-45-67
Email: info@salon.ru

## Правила записи

- Запись возможна за 14 дней вперед
- Отмена записи не позднее чем за 2 часа
- При опоздании более чем на 15 минут запись может быть отменена
"""
        
        sample_file = os.path.join(self.knowledge_base_path, "salon_info.md")
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        print(f"Создан пример базы знаний: {sample_file}")


# Функция для запуска загрузки базы знаний
async def main():
    kb_manager = KnowledgeBaseManager()
    
    # Создаем пример базы знаний если папка пуста
    if not kb_manager.get_all_markdown_files():
        kb_manager.create_sample_knowledge_base()
    
    # Загружаем базу знаний
    await kb_manager.load_knowledge_base()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 