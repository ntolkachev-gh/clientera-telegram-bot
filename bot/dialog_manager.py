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
            "telegram_id": client.telegram_id,
            "name": f"{client.first_name or ''} {client.last_name or ''}".strip(),
            "favorite_services": client.favorite_services or [],
            "favorite_masters": client.favorite_masters or [],
            "preferred_time_slots": client.preferred_time_slots or [],
            "custom_notes": client.custom_notes or {}
        }
        
        # Сначала проверяем, является ли это подтверждением записи (содержит дату и время)
        if self._is_booking_confirmation(message_text):
            return await self._handle_booking_confirmation(client_profile, message_text)

        # Получаем список услуг, чтобы передать его в GPT
        try:
            services_raw = await self.youclients_api.get_services()
            available_services = [s.get("title") for s in services_raw if s.get("title")]
        except Exception:
            available_services = []

        # Анализируем запрос с помощью GPT (без ручных ключевых слов)
        analysis = await self.openai_client.process_booking_request(
            message_text,
            client_profile,
            available_services
        )
        
        intent = analysis.get("intent", "other")
        
        if intent == "booking":
            return await self._handle_booking_request(analysis, client_profile)
        elif intent == "question":
            return await self._handle_question(message_text)
        else:
            return await self._handle_general_chat(message_text, client_profile)

    def _is_booking_request(self, message_text: str) -> bool:
        """Проверяет, является ли сообщение запросом на запись"""
        import re
        
        # Ключевые слова для записи
        booking_keywords = [
            'записаться', 'запись', 'хочу записаться', 'записаться к вам',
            'записаться на', 'записаться к мастеру', 'когда можно записаться',
            'есть ли свободное время', 'хочу прийти', 'когда можно прийти',
            'записаться в салон', 'записаться в салон красоты',
            'массаж', 'маникюр', 'педикюр', 'spa', 'спа', 'обертывание'
        ]
        
        message_lower = message_text.lower()
        
        # Проверяем наличие ключевых слов
        for keyword in booking_keywords:
            if keyword in message_lower:
                return True
        
        # Проверяем паттерны типа "хочу + услуга"
        service_patterns = [
            r'хочу\s+(стрижку|окрашивание|укладку|мелирование|массаж|маникюр|педикюр|spa|спа|обертывание)',
            r'нужна\s+(стрижка|окрашивание|укладка|мелирование|массаж|маникюр|педикюр|spa|спа|обертывание)',
            r'записаться\s+на\s+(стрижку|окрашивание|укладку|мелирование|массаж|маникюр|педикюр|spa|спа|обертывание)'
        ]
        
        for pattern in service_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False

    def _is_booking_confirmation(self, message_text: str) -> bool:
        """Проверяет, содержит ли сообщение информацию, достаточную для подтверждения записи"""
        import re
        # Если есть явные цифры даты и времени
        date_pattern = r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?"
        time_pattern = r"\d{1,2}[:.]\d{2}"
        if re.search(date_pattern, message_text) and re.search(time_pattern, message_text):
            return True

        # Дополнительная проверка на слова дня недели + часть дня (утром/днем/вечером)
        weekdays = [
            'понедельник', 'вторник', 'сред', 'четверг', 'пятниц', 'суббот', 'воскрес'
        ]
        if any(w in message_text.lower() for w in weekdays):
            if any(x in message_text.lower() for x in ['утр', 'дн', 'веч', 'ноч']):
                return True
        return False

    async def _handle_booking_request(self, analysis: Dict[str, Any], client_profile: Dict[str, Any]) -> str:
        """Обработка запроса на запись"""
        service_name = analysis.get("service")
        master_name = analysis.get("master")
        preferred_date = analysis.get("preferred_date")
        preferred_time = analysis.get("preferred_time")
        needs_clarification = analysis.get("needs_clarification", [])

        # Если все данные уже есть – создаём запись сразу
        if not needs_clarification and preferred_date and preferred_time:
            try:
                from datetime import datetime
                # Формируем datetime
                appointment_datetime = datetime.strptime(
                    f"{preferred_date} {preferred_time}", "%Y-%m-%d %H:%M"
                )
                # Дефолты, если GPT не распознал
                service = service_name or "Не указана"
                master = master_name or "Наш мастер"

                # Сохраняем в БД (локально)
                from database.models import Appointment, Client
                client_id = client_profile.get("id")
                client_obj = self.db.query(Client).filter(Client.id == client_id).first()
                if client_obj:
                    appointment = Appointment(
                        client_id=client_obj.id,
                        service_name=service,
                        master_name=master,
                        appointment_datetime=appointment_datetime,
                        duration_minutes=60,
                        status="scheduled"
                    )
                    self.db.add(appointment)
                    self.db.commit()
                    self.db.refresh(appointment)

                    return (
                        f"✅ Запись создана!\n\n"
                        f"📅 {appointment_datetime.strftime('%d.%m.%Y')}\n"
                        f"⏰ {appointment_datetime.strftime('%H:%M')}\n"
                        f"🎯 {service}\n"
                        f"👩‍💼 {master}\n\n"
                        "Если нужно изменить или отменить запись, дайте знать."
                    )
            except Exception as e:
                # Если что-то пошло не так – падаем в обычный поток слотов
                print(f"Ошибка автосоздания записи: {e}")
        
        # Если нужны уточнения
        if needs_clarification:
            clarification_text = "Для записи мне нужно уточнить:\n"
            for item in needs_clarification:
                clarification_text += f"• {item}\n"
            
            # Предлагаем варианты на основе локальных данных
            if "service" in str(needs_clarification).lower():
                clarification_text += "\nДоступные услуги:\n"
                clarification_text += "• Стрижка (1500 руб., 60 мин.)\n"
                clarification_text += "• Окрашивание (3000 руб., 120 мин.)\n"
                clarification_text += "• Укладка (2000 руб., 90 мин.)\n"
                clarification_text += "• Мелирование (4000 руб., 150 мин.)\n"
            
            if "master" in str(needs_clarification).lower():
                clarification_text += "\nНаши мастера:\n"
                clarification_text += "• Анна Петрова (парикмахер)\n"
                clarification_text += "• Мария Иванова (стилист)\n"
                clarification_text += "• Елена Сидорова (мастер по окрашиванию)\n"
            
            return clarification_text
        
        # Генерируем доступные слоты на основе предпочтений
        available_slots = await self._generate_available_slots(preferred_date, preferred_time)
        
        if not available_slots:
            return f"К сожалению, нет свободных слотов на указанное время. Попробуйте другой день или время."
        
        # Форматируем доступные слоты
        service_display = service_name or "выбранную услугу"
        master_display = master_name or "нашего мастера"
        
        slots_text = f"Отлично! Нашел свободные слоты для записи к {master_display} на {service_display}:\n\n"
        for slot in available_slots[:5]:  # Показываем первые 5 слотов
            slots_text += f"• {slot['date']} в {slot['time']}\n"
        
        slots_text += f"\n💡 Стоимость услуги: уточните в салоне\n"
        slots_text += f"⏱ Длительность: 60-120 мин. (зависит от услуги)\n\n"
        slots_text += "Напишите желаемую дату и время для подтверждения записи."
        
        return slots_text

    async def _handle_booking_confirmation(self, client_profile: Dict[str, Any], message_text: str) -> str:
        """Обработка подтверждения записи"""
        # Пытаемся извлечь дату и время из сообщения
        from datetime import datetime
        import re
        
        # Простые паттерны для поиска даты и времени
        date_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 17.07.2025
            r'(\d{1,2})\.(\d{1,2})',  # 17.07 (текущий год)
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 17/07/2025
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 17-07-2025
        ]
        
        time_patterns = [
            r'(\d{1,2}):(\d{2})',  # 14:30
            r'(\d{1,2})\.(\d{2})',  # 14.30
        ]
        
        # Ищем дату или день недели
        appointment_date = None
        for pattern in date_patterns:
            match = re.search(pattern, message_text)
            if match:
                if len(match.groups()) == 3:
                    day, month, year = match.groups()
                else:
                    day, month = match.groups()
                    year = datetime.now().year
                try:
                    appointment_date = datetime(int(year), int(month), int(day))
                    break
                except ValueError:
                    continue
        
        # Ищем время
        appointment_time = None
        for pattern in time_patterns:
            match = re.search(pattern, message_text)
            if match:
                hour, minute = match.groups()
                try:
                    appointment_time = datetime.now().replace(hour=int(hour), minute=int(minute))
                    break
                except ValueError:
                    continue
        
        if not appointment_date:
            # Если дата не найдена, попробуем распознать по дню недели
            weekday_map = {
                'понедельник': 0,
                'вторник': 1,
                'сред': 2,
                'четверг': 3,
                'пятниц': 4,
                'суббот': 5,
                'воскрес': 6
            }
            for wkey, wval in weekday_map.items():
                if wkey in message_text.lower():
                    from datetime import timedelta
                    today = datetime.now()
                    days_ahead = (wval - today.weekday()) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # следующая неделя
                    appointment_date = (today + timedelta(days=days_ahead)).replace(hour=0, minute=0)
                    break

        # Если время не указано словами, задаём по части дня
        if not appointment_time:
            lower_msg = message_text.lower()
            if any(word in lower_msg for word in ['утр', 'утром', 'утро']):
                appointment_time = datetime.now().replace(hour=10, minute=0)
            elif any(word in lower_msg for word in ['дн', 'днем', 'днём', 'день']):
                appointment_time = datetime.now().replace(hour=13, minute=0)
            elif any(word in lower_msg for word in ['веч', 'вечер', 'вечером']):
                appointment_time = datetime.now().replace(hour=18, minute=0)

        # Всё ещё нет даты или времени?
        if not appointment_date:
            return "Пожалуйста, укажите точную дату (например, 20.07.2025) или день недели."

        if not appointment_time:
            return "Пожалуйста, уточните время (например, 14:30, утро, день, вечер)."
        
        # Создаем полную дату и время
        appointment_datetime = appointment_date.replace(
            hour=appointment_time.hour,
            minute=appointment_time.minute
        )
        
        # Проверяем, что время в будущем
        if appointment_datetime <= datetime.now():
            return "Пожалуйста, выберите время в будущем."
        
        # Создаем запись в локальной базе данных
        try:
            from database.models import Appointment, Client
            
            # Находим клиента в базе данных
            client = self.db.query(Client).filter(
                Client.telegram_id == client_profile.get("telegram_id")
            ).first()
            
            if not client:
                return "Ошибка: клиент не найден в базе данных."
            
            # Определяем услугу и мастера на основе контекста или используем значения по умолчанию
            service_name = "Стрижка"  # Можно улучшить, анализируя предыдущие сообщения
            master_name = "Анна Петрова"  # Можно улучшить, анализируя предыдущие сообщения
            
            # Создаем запись в локальной БД
            appointment = Appointment(
                client_id=client.id,
                service_name=service_name,
                master_name=master_name,
                appointment_datetime=appointment_datetime,
                duration_minutes=60,  # По умолчанию
                status="scheduled"
            )
            
            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)
            
            return f"""✅ Запись успешно создана!

📅 Дата: {appointment_datetime.strftime('%d.%m.%Y')}
⏰ Время: {appointment_datetime.strftime('%H:%M')}
🎯 Услуга: {service_name}
👩‍💼 Мастер: {master_name}
💰 Стоимость: уточните в салоне
⏱ Длительность: 60 мин.

Запись сохранена в нашей системе. Ждем вас в салоне!
Если нужно изменить или отменить запись, свяжитесь с нами."""
                
        except Exception as e:
            return f"Ошибка при создании записи: {str(e)}. Пожалуйста, попробуйте позже."

    async def _generate_available_slots(self, preferred_date: str = None, preferred_time: str = None) -> List[Dict[str, Any]]:
        """Генерация доступных слотов на основе предпочтений"""
        from datetime import datetime, timedelta
        
        slots = []
        start_date = datetime.now()
        
        # Если указана предпочтительная дата, начинаем с неё
        if preferred_date:
            try:
                # Пытаемся распарсить дату в разных форматах
                for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        start_date = datetime.strptime(preferred_date, fmt)
                        break
                    except ValueError:
                        continue
            except:
                start_date = datetime.now()
        
        # Генерируем слоты на следующие 7 дней
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            
            # Пропускаем выходные (суббота и воскресенье)
            if current_date.weekday() >= 5:
                continue
            
            # Генерируем временные слоты с 9:00 до 19:00
            for hour in range(9, 19):
                for minute in [0, 30]:  # Каждые полчаса
                    time_str = f"{hour:02d}:{minute:02d}"
                    
                    # Если указано предпочтительное время, приоритизируем его
                    if preferred_time and preferred_time in time_str:
                        slots.insert(0, {
                            "date": current_date.strftime("%d.%m.%Y"),
                            "time": time_str,
                            "datetime": current_date.replace(hour=hour, minute=minute)
                        })
                    else:
                        slots.append({
                            "date": current_date.strftime("%d.%m.%Y"),
                            "time": time_str,
                            "datetime": current_date.replace(hour=hour, minute=minute)
                        })
        
        return slots[:10]  # Возвращаем первые 10 слотов

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
            "content": f"""Ты — дружелюбный и профессиональный ассистент салона красоты.\n\nПравила ответа:\n1. Используй эмодзи, чтобы выделять ключевые моменты (но не перегружай).\n2. Структурируй ответ: короткие абзацы, списки через •.\n3. Если предлагаешь варианты даты/времени или услуг — выводи их на отдельных строках.\n4. Всегда отвечай на русском.\n5. Если нужна дополнительная информация для записи — чётко перечисли, что ещё уточнить.\n\nКонтекст о клиенте:\n• Имя клиента: {client_profile['name'] or 'Неизвестно'}\n• Любимые услуги: {', '.join(client_profile['favorite_services']) or 'нет данных'}\n• Любимые мастера: {', '.join(client_profile['favorite_masters']) or 'нет данных'}\n• Предпочитаемое время: {', '.join(client_profile['preferred_time_slots']) or 'нет данных'}\n\nВсегда будь приветлив и помогай клиенту оформить запись или найти информацию."""
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