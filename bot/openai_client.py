import openai
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from config import settings
from database.models import OpenAIUsageLog, Client

# Настройка OpenAI клиента
openai.api_key = settings.openai_api_key

# Цены на токены (в долларах за 1000 токенов)
PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "text-embedding-3-small": {"input": 0.0002, "output": 0.0}
}


class OpenAIClient:
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def _log_usage(self, client_id: Optional[int], model: str, purpose: str, 
                   prompt_tokens: int, completion_tokens: int, total_tokens: int):
        """Логирование использования OpenAI API"""
        cost = 0.0
        if model in PRICING:
            cost = (prompt_tokens * PRICING[model]["input"] + 
                   completion_tokens * PRICING[model]["output"]) / 1000
        
        usage_log = OpenAIUsageLog(
            client_id=client_id,
            model=model,
            purpose=purpose,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost
        )
        self.db.add(usage_log)
        self.db.commit()

    async def chat_completion(self, messages: List[Dict[str, str]], 
                            client_id: Optional[int] = None, 
                            model: str = "gpt-4") -> str:
        """Получение ответа от GPT модели"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Логирование использования
            usage = response.usage
            self._log_usage(
                client_id=client_id,
                model=model,
                purpose="chat",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Ошибка при обращении к OpenAI: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."

    async def extract_facts(self, conversation_history: str, 
                          client_id: Optional[int] = None) -> Dict[str, Any]:
        """Извлечение фактов о клиенте из истории разговора"""
        prompt = f"""
        Проанализируй следующий разговор с клиентом салона красоты и извлеки полезную информацию:
        
        {conversation_history}
        
        Верни JSON с информацией о клиенте:
        {{
            "favorite_services": ["список предпочитаемых услуг"],
            "favorite_masters": ["список предпочитаемых мастеров"],
            "preferred_time_slots": ["предпочитаемое время записи"],
            "custom_notes": {{
                "allergies": "аллергии или противопоказания",
                "preferences": "особые пожелания",
                "other": "другая важная информация"
            }}
        }}
        
        Если информация отсутствует, оставь поле пустым.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            # Логирование использования
            usage = response.usage
            self._log_usage(
                client_id=client_id,
                model="gpt-4",
                purpose="fact_extraction",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Ошибка при извлечении фактов: {e}")
            return {}

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для текстов"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            # Логирование использования
            total_tokens = response.usage.total_tokens
            self._log_usage(
                client_id=None,
                model="text-embedding-3-small",
                purpose="embedding",
                prompt_tokens=total_tokens,
                completion_tokens=0,
                total_tokens=total_tokens
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            print(f"Ошибка при создании эмбеддингов: {e}")
            return []

    async def process_booking_request(self, user_message: str, 
                                    client_profile: Dict[str, Any],
                                    available_services: List[str] | None = None) -> Dict[str, Any]:
        """Обработка запроса на запись с учетом профиля клиента"""
        # Добавляем список услуг, известный боту (если передан)
        services_list_text = ", ".join(available_services) if available_services else "неизвестно"

        prompt = f"""
        Клиент салона красоты написал: "{user_message}"
        
        Профиль клиента:
        - Любимые услуги: {client_profile.get('favorite_services', [])}
        - Любимые мастера: {client_profile.get('favorite_masters', [])}
        - Предпочитаемое время: {client_profile.get('preferred_time_slots', [])}

        Доступные услуги салона: {services_list_text}
        
        ВАЖНО: Если клиент хочет записаться на услугу (даже если не указал конкретную услугу или время), 
        то intent должен быть "booking". Ключевые слова для записи:
        - "записаться", "запись", "записаться к вам", "хочу записаться"
        - "записаться на стрижку", "записаться к мастеру"
        - "когда можно записаться", "есть ли свободное время"
        - "хочу прийти", "когда можно прийти"
        
        Проанализируй запрос и верни JSON:
        {{
            "intent": "booking|question|other",
            "service": "название услуги или null",
            "master": "имя мастера или null",
            "preferred_date": "дата в формате YYYY-MM-DD или null",
            "preferred_time": "время в формате HH:MM или null",
            "confidence": 0.8,
            "needs_clarification": ["список того, что нужно уточнить"],
            "response": "ответ клиенту"
        }}
        
        Если intent = "booking", то в needs_clarification укажи что нужно уточнить:
        - Если не указана услуга: "service"
        - Если не указан мастер: "master" 
        - Если не указана дата: "date"
        - Если не указано время: "time"
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            # Логирование использования
            usage = response.usage
            self._log_usage(
                client_id=client_profile.get('id'),
                model="gpt-4",
                purpose="booking_analysis",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Добавляем логирование для отладки
            print(f"🔍 Анализ запроса: '{user_message}' -> intent: {result.get('intent')}")
            
            return result
            
        except Exception as e:
            print(f"Ошибка при обработке запроса на запись: {e}")
            return {
                "intent": "other",
                "confidence": 0.0,
                "response": "Извините, произошла ошибка при обработке вашего запроса."
            } 