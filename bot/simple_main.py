import asyncio
import logging
import nest_asyncio
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database.database import SessionLocal, init_db
from database.models import Client, Session as ChatSession, Message
from bot.openai_client import OpenAIClient
from bot.youclients_api import YouclientsAPI
from config import settings
from typing import Optional

# Применяем nest_asyncio для решения проблем с event loop
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SimpleTelegramBot:
    def __init__(self):
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        welcome_message = f"""
👋 Добро пожаловать в салон красоты, {user.first_name}!

Это тестовая версия бота. Я могу:
• 💬 Общаться с вами
• 🤖 Отвечать на вопросы с помощью GPT-4
• 💾 Запоминать нашу переписку

Напишите мне что-нибудь, и я отвечу!
        """
        
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """
🤖 Тестовая версия бота

Доступные команды:
• /start - приветствие
• /help - эта справка

Просто напишите мне сообщение, и я отвечу с помощью GPT-4! 😊
        """
        await update.message.reply_text(help_text)

    def get_or_create_client(self, telegram_id: str, user_data: dict):
        """Получение или создание клиента"""
        with SessionLocal() as db:
            client = db.query(Client).filter(Client.telegram_id == telegram_id).first()
            
            if not client:
                client = Client(
                    telegram_id=telegram_id,
                    username=user_data.get("username"),
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name")
                )
                db.add(client)
                db.commit()
                db.refresh(client)
            
            return client

    async def process_appointment_booking(self, message_text: str, client: Client) -> Optional[str]:
        """Обработка записи на услуги и создание записи в Youclients"""
        try:
            # Простой парсинг для определения намерения записи
            booking_keywords = ['записать', 'записаться', 'запись', 'хочу записаться', 'запиши']
            service_keywords = ['массаж', 'обертывание', 'спа', 'процедура', 'маникюр', 'педикюр']
            
            is_booking = any(keyword in message_text.lower() for keyword in booking_keywords)
            has_service = any(keyword in message_text.lower() for keyword in service_keywords)
            
            if is_booking and has_service:
                # Создаем запись в Youclients
                youclients_api = YouclientsAPI()
                
                # Определяем услугу по тексту
                service_name = None
                if 'массаж' in message_text.lower():
                    service_name = 'массаж'
                elif 'обертывание' in message_text.lower():
                    service_name = 'обертывание'
                elif 'спа' in message_text.lower():
                    service_name = 'спа-процедура'
                
                if service_name:
                    # Ищем услугу в Youclients
                    service = await youclients_api.find_service_by_name(service_name)
                    if service:
                        # Получаем список мастеров
                        masters = await youclients_api.get_masters()
                        if masters:
                            # Берем первого доступного мастера
                            master = masters[0]
                            
                            # Назначаем время на завтра в 10:00
                            tomorrow = datetime.now() + timedelta(days=1)
                            appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                            
                            # Создаем запись
                            client_data = {
                                "name": f"{client.first_name or ''} {client.last_name or ''}".strip(),
                                "phone": "",  # Нужно будет добавить сбор телефона
                                "email": "",
                                "comment": f"Запись через Telegram бота. Сообщение: {message_text}"
                            }
                            
                            result = await youclients_api.create_appointment(
                                client_data, 
                                service["id"], 
                                master["id"], 
                                appointment_time
                            )
                            
                            if result.get("success"):
                                return f"✅ Отлично! Я создал запись на {service_name} на завтра в 10:00. Запись подтверждена в системе."
                            else:
                                return f"❌ К сожалению, не удалось создать запись. Ошибка: {result.get('error', 'Неизвестная ошибка')}"
                
                return "Я понял, что вы хотите записаться. Пожалуйста, уточните, на какую именно услугу вы хотели бы записаться?"
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при обработке записи: {e}")
            return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Получаем или создаем клиента
            user_data = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            client = self.get_or_create_client(str(user.id), user_data)
            
            # Сохраняем сообщение пользователя
            with SessionLocal() as db:
                # Создаем простую сессию
                session = ChatSession(
                    client_id=client.id,
                    is_active=True
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
                # Сохраняем сообщение пользователя
                user_message = Message(
                    client_id=client.id,
                    session_id=session.id,
                    message_type="user",
                    content=message_text,
                    telegram_message_id=update.message.message_id
                )
                db.add(user_message)
                db.commit()
                
                # Получаем ответ от GPT-4
                openai_client = OpenAIClient(db)
                
                # Получаем историю сообщений для контекста
                recent_messages = db.query(Message).filter(
                    Message.client_id == client.id
                ).order_by(Message.created_at.desc()).limit(10).all()
                
                # Создаем список сообщений с историей
                messages = [
                    {
                        "role": "system",
                        "content": f"""Ты - дружелюбный помощник в салоне красоты. 
                        Общайся с клиентом {client.first_name or 'дорогой клиент'} тепло и профессионально.
                        Отвечай на вопросы о салоне, услугах, записи.
                        Если не знаешь точной информации, честно скажи об этом.
                        Важно: помни контекст разговора и не спрашивай информацию, которую клиент уже предоставил."""
                    }
                ]
                
                # Добавляем историю сообщений (в обратном порядке)
                for msg in reversed(recent_messages):
                    if msg.message_type == "user":
                        messages.append({"role": "user", "content": msg.content})
                    elif msg.message_type == "bot":
                        messages.append({"role": "assistant", "content": msg.content})
                
                # Добавляем текущее сообщение пользователя
                messages.append({"role": "user", "content": message_text})
                
                # Проверяем, не является ли это записью на услугу
                appointment_response = await self.process_appointment_booking(message_text, client)
                
                if appointment_response:
                    # Если это запись, отправляем ответ сразу
                    response = appointment_response
                else:
                    # Иначе получаем ответ от GPT-4
                    response = await openai_client.chat_completion(messages, client.id)
                
                # Сохраняем ответ бота
                bot_message = Message(
                    client_id=client.id,
                    session_id=session.id,
                    message_type="bot",
                    content=response
                )
                db.add(bot_message)
                db.commit()
                
                await update.message.reply_text(response)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего сообщения. "
                "Попробуйте еще раз или обратитесь к администратору."
            )

    async def run(self):
        """Запуск бота"""
        logger.info("Запуск простого Telegram бота...")
        
        # Инициализация базы данных
        init_db()
        
        # Запуск бота
        await self.application.run_polling(drop_pending_updates=True)


async def main():
    """Главная функция"""
    bot = SimpleTelegramBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise 