from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from database.models import Client, Session as ChatSession, Message
from bot.openai_client import OpenAIClient
from bot.youclients_api import YouclientsAPI
from bot.embedding import KnowledgeBaseManager
from config import settings


class DialogManager:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAIClient(db)
        self.youclients_api = YouclientsAPI()
        self.kb_manager = KnowledgeBaseManager()
        self.session_timeout = timedelta(hours=settings.session_timeout_hours)

    def get_or_create_client(self, telegram_id: str, user_data: Dict[str, Any]) -> Client:
        """Получение или создание клиента"""
        client = self.db.query(Client).filter(Client.telegram_id == telegram_id).first()
        
        if not client:
            client = Client(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name")
            )
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
        
        return client

    def get_or_create_session(self, client_id: int) -> ChatSession:
        """Получение или создание сессии"""
        # Ищем активную сессию
        active_session = self.db.query(ChatSession).filter(
            ChatSession.client_id == client_id,
            ChatSession.is_active == True
        ).first()
        
        # Проверяем, не истекла ли сессия
        if active_session:
            last_message = self.db.query(Message).filter(
                Message.session_id == active_session.id
            ).order_by(Message.created_at.desc()).first()
            
            if last_message:
                time_since_last = datetime.utcnow() - last_message.created_at
                if time_since_last > self.session_timeout:
                    # Закрываем старую сессию
                    active_session.is_active = False
                    active_session.session_end = datetime.utcnow()
                    active_session = None
        
        # Создаем новую сессию если нужно
        if not active_session:
            active_session = ChatSession(
                client_id=client_id,
                session_start=datetime.utcnow(),
                is_active=True
            )
            self.db.add(active_session)
            self.db.commit()
            self.db.refresh(active_session)
        
        return active_session

    def save_message(self, client_id: int, session_id: int, message_type: str, 
                    content: str, telegram_message_id: Optional[int] = None) -> Message:
        """Сохранение сообщения"""
        message = Message(
            client_id=client_id,
            session_id=session_id,
            message_type=message_type,
            content=content,
            telegram_message_id=telegram_message_id
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_session_history(self, session_id: int, limit: int = 10) -> List[Message]:
        """Получение истории сессии"""
        return self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

    def format_conversation_history(self, messages: List[Message]) -> str:
        """Форматирование истории разговора для анализа"""
        formatted = []
        for message in reversed(messages):  # Сортируем по времени
            role = "Клиент" if message.message_type == "user" else "Бот"
            formatted.append(f"{role}: {message.content}")
        
        return "\n".join(formatted)

    async def extract_and_update_client_facts(self, client_id: int, session_id: int):
        """Извлечение и обновление фактов о клиенте"""
        # Получаем историю сессии
        messages = self.get_session_history(session_id, limit=20)
        
        if len(messages) < 2:  # Нужно минимум 2 сообщения для анализа
            return
        
        # Форматируем историю
        conversation_history = self.format_conversation_history(messages)
        
        # Извлекаем факты
        facts = await self.openai_client.extract_facts(conversation_history, client_id)
        
        if not facts:
            return
        
        # Обновляем профиль клиента
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if client:
            # Обновляем предпочтения
            if facts.get("favorite_services"):
                current_services = client.favorite_services or []
                new_services = facts["favorite_services"]
                updated_services = list(set(current_services + new_services))
                client.favorite_services = updated_services
            
            if facts.get("favorite_masters"):
                current_masters = client.favorite_masters or []
                new_masters = facts["favorite_masters"]
                updated_masters = list(set(current_masters + new_masters))
                client.favorite_masters = updated_masters
            
            if facts.get("preferred_time_slots"):
                current_slots = client.preferred_time_slots or []
                new_slots = facts["preferred_time_slots"]
                updated_slots = list(set(current_slots + new_slots))
                client.preferred_time_slots = updated_slots
            
            # Обновляем заметки
            if facts.get("custom_notes"):
                current_notes = client.custom_notes or {}
                new_notes = facts["custom_notes"]
                current_notes.update(new_notes)
                client.custom_notes = current_notes
            
            client.updated_at = datetime.utcnow()
            self.db.commit()

    async def process_message(self, telegram_id: str, user_data: Dict[str, Any], 
                            message_text: str, telegram_message_id: Optional[int] = None) -> str:
        """Основная обработка сообщения"""
        # Получаем или создаем клиента
        client = self.get_or_create_client(telegram_id, user_data)
        
        # Получаем или создаем сессию
        session = self.get_or_create_session(client.id)
        
        # Сохраняем сообщение пользователя
        self.save_message(client.id, session.id, "user", message_text, telegram_message_id)
        
        # Определяем тип запроса
        response = await self._handle_message_type(client, session, message_text)
        
        # Сохраняем ответ бота
        self.save_message(client.id, session.id, "bot", response)
        
        # Извлекаем факты в фоне (можно сделать асинхронно)
        try:
            await self.extract_and_update_client_facts(client.id, session.id)
        except Exception as e:
            print(f"Ошибка при извлечении фактов: {e}")
        
        return response

    async def _handle_message_type(self, client: Client, session: ChatSession, message_text: str) -> str:
        """Определение типа сообщения и обработка"""
        # Подготавливаем профиль клиента
        client_profile = {
            "id": client.id,
            "name": f"{client.first_name or ''} {client.last_name or ''}".strip(),
            "favorite_services": client.favorite_services or [],
            "favorite_masters": client.favorite_masters or [],
            "preferred_time_slots": client.preferred_time_slots or [],
            "custom_notes": client.custom_notes or {}
        }
        
        # Анализируем запрос с помощью GPT
        analysis = await self.openai_client.process_booking_request(message_text, client_profile)
        
        intent = analysis.get("intent", "other")
        
        if intent == "booking":
            return await self._handle_booking_request(analysis, client_profile)
        elif intent == "question":
            return await self._handle_question(message_text)
        else:
            return await self._handle_general_chat(message_text, client_profile)

    async def _handle_booking_request(self, analysis: Dict[str, Any], client_profile: Dict[str, Any]) -> str:
        """Обработка запроса на запись"""
        service_name = analysis.get("service")
        master_name = analysis.get("master")
        preferred_date = analysis.get("preferred_date")
        preferred_time = analysis.get("preferred_time")
        needs_clarification = analysis.get("needs_clarification", [])
        
        # Если нужны уточнения
        if needs_clarification:
            clarification_text = "Для записи мне нужно уточнить:\n"
            for item in needs_clarification:
                clarification_text += f"• {item}\n"
            
            # Предлагаем варианты на основе доступных услуг/мастеров
            if "service" in str(needs_clarification).lower():
                services_list = await self.youclients_api.format_services_list()
                clarification_text += f"\n{services_list}"
            
            if "master" in str(needs_clarification).lower():
                masters_list = await self.youclients_api.format_masters_list()
                clarification_text += f"\n{masters_list}"
            
            return clarification_text
        
        # Пытаемся найти услугу и мастера
        service = None
        master = None
        
        if service_name:
            service = await self.youclients_api.find_service_by_name(service_name)
        
        if master_name:
            master = await self.youclients_api.find_master_by_name(master_name)
        
        if not service:
            return "Не удалось найти указанную услугу. Пожалуйста, выберите из доступных:\n\n" + \
                   await self.youclients_api.format_services_list()
        
        if not master:
            return "Не удалось найти указанного мастера. Пожалуйста, выберите из доступных:\n\n" + \
                   await self.youclients_api.format_masters_list()
        
        # Получаем доступные слоты
        available_slots = await self.youclients_api.get_next_available_slots(
            service["id"], master["id"], days_ahead=7
        )
        
        if not available_slots:
            return f"К сожалению, у мастера {master_name} нет свободных слотов на ближайшие 7 дней."
        
        # Форматируем доступные слоты
        slots_text = f"Доступные слоты для записи к {master_name} на {service_name}:\n\n"
        for slot in available_slots[:10]:  # Показываем первые 10 слотов
            slots_text += f"• {slot['date']} в {slot['time']}\n"
        
        slots_text += "\nНапишите желаемую дату и время для записи."
        
        return slots_text

    async def _handle_question(self, message_text: str) -> str:
        """Обработка вопроса через базу знаний"""
        return await self.kb_manager.answer_question(message_text)

    async def _handle_general_chat(self, message_text: str, client_profile: Dict[str, Any]) -> str:
        """Обработка обычного чата"""
        # Получаем историю для контекста
        recent_messages = self.get_session_history(client_profile["id"], limit=5)
        
        # Формируем контекст
        context_messages = []
        for msg in reversed(recent_messages):
            role = "user" if msg.message_type == "user" else "assistant"
            context_messages.append({"role": role, "content": msg.content})
        
        # Системное сообщение
        system_message = {
            "role": "system",
            "content": f"""Ты - помощник в салоне красоты. 
            Общайся дружелюбно и профессионально с клиентом {client_profile['name']}.
            Помогай с записью на услуги, отвечай на вопросы о салоне.
            Если клиент хочет записаться, уточни услугу, мастера и время.
            
            Информация о клиенте:
            - Любимые услуги: {client_profile['favorite_services']}
            - Любимые мастера: {client_profile['favorite_masters']}
            - Предпочитаемое время: {client_profile['preferred_time_slots']}
            """
        }
        
        messages = [system_message] + context_messages + [{"role": "user", "content": message_text}]
        
        return await self.openai_client.chat_completion(messages, client_profile["id"])

    def close_session(self, session_id: int):
        """Закрытие сессии"""
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.is_active = False
            session.session_end = datetime.utcnow()
            self.db.commit()

    def get_client_stats(self, client_id: int) -> Dict[str, Any]:
        """Получение статистики клиента"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {}
        
        sessions_count = self.db.query(ChatSession).filter(
            ChatSession.client_id == client_id
        ).count()
        
        messages_count = self.db.query(Message).filter(
            Message.client_id == client_id
        ).count()
        
        return {
            "client_id": client_id,
            "telegram_id": client.telegram_id,
            "name": f"{client.first_name or ''} {client.last_name or ''}".strip(),
            "sessions_count": sessions_count,
            "messages_count": messages_count,
            "last_visit": client.last_visit_date,
            "favorite_services": client.favorite_services,
            "favorite_masters": client.favorite_masters,
            "created_at": client.created_at
        } 