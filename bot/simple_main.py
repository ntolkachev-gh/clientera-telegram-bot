import asyncio
import logging
import nest_asyncio
import os
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database.database import SessionLocal, init_db
from database.models import Client, Session as ChatSession, Message
from core.openai_client import OpenAIClient
from core.yclients_client import YclientsClient
from bot.youclients_api import YouclientsAPI
from config import settings
from prompts import format_prompt, PromptNames
from typing import Optional

# Применяем nest_asyncio для решения проблем с event loop только в локальной среде
if os.getenv('HEROKU') is None:
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
Добро пожаловать в салон красоты, {user.first_name}!

Я помогу вам:
• Записаться на услуги
• Ответить на вопросы о салоне
• Выбрать подходящего мастера
• Найти удобное время

Просто напишите что вас интересует, например:
"Хочу записаться на маникюр к Наталье на завтра"

Или воспользуйтесь командами:
/services - список услуг
/masters - наши мастера
/profile - ваш профиль
/help - помощь
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """
Как пользоваться ботом:

**Запись на услуги:**
• "Хочу записаться на маникюр"
• "Запиши меня к Наталье на завтра в 15:00"
• "Нужен педикюр на пятницу"

**Вопросы о салоне:**
• "Сколько стоит маникюр?"
• "Какие у вас есть услуги?"
• "Где находится салон?"

**Профиль:**
• /profile - посмотреть свой профиль
• Бот запоминает ваши предпочтения

**Команды:**
• /start - главное меню
• /services - список услуг
• /masters - наши мастера
• /help - эта справка

Просто пишите естественным языком, я пойму!
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
            logger.info(f"Проверяем сообщение на запись: {message_text}")

            # Простой парсинг для определения намерения записи
            booking_keywords = ['записать', 'записаться', 'запись', 'хочу записаться', 'запиши']
            service_keywords = ['массаж', 'обертывание', 'спа', 'процедура', 'маникюр', 'педикюр']

            is_booking = any(keyword in message_text.lower() for keyword in booking_keywords)
            has_service = any(keyword in message_text.lower() for keyword in service_keywords)

            logger.info(f"is_booking: {is_booking}, has_service: {has_service}")

            if is_booking and has_service:
                logger.info("Обнаружена попытка записи, создаем запись в Youclients")

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

                logger.info(f"Определена услуга: {service_name}")

                if service_name:
                    # Ищем услугу в Youclients
                    logger.info("Ищем услугу в Youclients API")
                    service = await youclients_api.find_service_by_name(service_name)
                    logger.info(f"Найдена услуга: {service}")

                    if service:
                        # Получаем список мастеров
                        logger.info("Получаем список мастеров")
                        masters = await youclients_api.get_masters()
                        logger.info(f"Найдено мастеров: {len(masters) if masters else 0}")

                        if masters:
                            # Берем первого доступного мастера
                            master = masters[0]
                            logger.info(f"Выбран мастер: {master}")

                            # Назначаем время на завтра в 10:00
                            tomorrow = datetime.now() + timedelta(days=1)
                            appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                            logger.info(f"Время записи: {appointment_time}")

                            # Создаем запись
                            client_data = {
                                "name": f"{client.first_name or ''} {client.last_name or ''}".strip(),
                                "phone": "",  # Нужно будет добавить сбор телефона
                                "email": "",
                                "comment": f"Запись через Telegram бота. Сообщение: {message_text}"
                            }

                            logger.info(f"Создаем запись с данными: {client_data}")
                            result = await youclients_api.create_appointment(
                                client_data,
                                service["id"],
                                master["id"],
                                appointment_time
                            )

                            logger.info(f"Результат создания записи: {result}")

                            if result.get("success"):
                                return f"✅ Отлично! Я создал запись на {service_name} на завтра в 10:00. Запись подтверждена в системе."
                            else:
                                return f"❌ К сожалению, не удалось создать запись. Ошибка: {result.get('error', 'Неизвестная ошибка')}"
                        else:
                            logger.warning("Не найдено мастеров в Youclients")
                    else:
                        logger.warning(f"Услуга '{service_name}' не найдена в Youclients")

                return "Я понял, что вы хотите записаться. Пожалуйста, уточните, на какую именно услугу вы хотели бы записаться?"

            logger.info("Сообщение не является записью на услугу")
            return None

        except Exception as e:
            logger.error(f"Ошибка при обработке записи: {e}")
            return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user = update.effective_user if update.effective_user else None
        message_text = update.message.text if update.message else None
        if not user or not message_text:
            return
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        try:
            user_data = {
                "username": getattr(user, "username", None),
                "first_name": getattr(user, "first_name", None),
                "last_name": getattr(user, "last_name", None)
            }
            client = self.get_or_create_client(str(user.id), user_data)
            with SessionLocal() as db:
                # Получаем актуального клиента из БД (объект, а не колонку)
                client_db = db.query(Client).filter(Client.telegram_id == str(user.id)).first()
                if client_db is None:
                    # Если клиента нет, создаём и повторно получаем
                    new_client = Client(
                        telegram_id=str(user.id),
                        username=user_data.get("username"),
                        first_name=user_data.get("first_name"),
                        last_name=user_data.get("last_name")
                    )
                    db.add(new_client)
                    db.commit()
                    db.refresh(new_client)
                    client_db = new_client
                if client_db is None:
                    logger.error("Не удалось получить или создать клиента")
                    return
                session = ChatSession(
                    client_id=client_db.id,
                    is_active=True
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                user_message = Message(
                    client_id=client_db.id,
                    session_id=session.id,
                    message_type="user",
                    content=message_text,
                    telegram_message_id=update.message.message_id if update.message else None
                )
                db.add(user_message)
                db.commit()

                # Инициализация YClients клиента для tools
                yclients_client = YclientsClient(
                    api_key=settings.youclients_api_key,
                    company_id=settings.youclients_company_id
                )
                openai_client = OpenAIClient(db, yclients_client)
                recent_messages = db.query(Message).filter(
                    Message.client_id == client_db.id
                ).order_by(Message.created_at.desc()).limit(10).all()
                # Загружаем системный промпт из файла
                try:
                    system_prompt = format_prompt(
                        PromptNames.SALON_RESPONSE_SYSTEM,
                        client_name=client_db.first_name or 'Неизвестно',
                        favorite_services=', '.join(getattr(client_db, 'favorite_services', []) or []) or 'нет данных',
                        favorite_masters=', '.join(getattr(client_db, 'favorite_masters', []) or []) or 'нет данных',
                        preferred_time_slots=', '.join(getattr(client_db, 'preferred_time_slots', []) or []) or 'нет данных'
                    )
                except Exception as e:
                    logger.error(f"SM_ERR: Ошибка загрузки промпта: {e}")
                    # Fallback к простому промпту без эмодзи
                    system_prompt = """Ты — профессиональный ассистент салона красоты.
Отвечай коротко и по делу, без эмодзи.
Помогай клиенту записаться или получить информацию."""
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                # Гарантируем, что recent_messages — это список объектов Message
                for msg in reversed(recent_messages):
                    if hasattr(msg, 'message_type') and hasattr(msg, 'content') and isinstance(msg.content, str):
                        if msg.message_type == "user":
                            messages.append({"role": "user", "content": msg.content})
                        elif msg.message_type == "bot":
                            messages.append({"role": "assistant", "content": msg.content})
                messages.append({"role": "user", "content": message_text})
                appointment_response = await self.process_appointment_booking(message_text, client_db)
                if appointment_response:
                    response = appointment_response
                else:
                    cid = getattr(client_db, 'id', None)
                    response = await openai_client.chat_completion_with_tools(messages, int(cid) if isinstance(cid, int) else None)
                bot_message = Message(
                    client_id=client_db.id if hasattr(client_db, 'id') else None,
                    session_id=session.id,
                    message_type="bot",
                    content=response
                )
                db.add(bot_message)
                db.commit()
                if update.message:
                    await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            if update.message:
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
        # Определяем среду запуска
        heroku_env = os.getenv('HEROKU') is not None or os.getenv('DYNO') is not None
        logger.info(f"SM_MAIN: Запуск в среде: {'Heroku' if heroku_env else 'Local'}")

        if heroku_env:
            # Heroku environment - используем простой запуск без nest_asyncio
            logger.info("SM_MAIN: Создаем новый event loop для Heroku")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.info("SM_MAIN: Запускаем main() в Heroku loop")
                loop.run_until_complete(main())
            finally:
                logger.info("SM_MAIN: Закрываем Heroku loop")
                loop.close()
        else:
            # Local environment
            logger.info("SM_MAIN: Запускаем в локальной среде")
            asyncio.run(main())
    except Exception as e:
        logger.error(f"SM_MAIN: Критическая ошибка запуска бота: {e}")
        logger.error(f"SM_MAIN: Тип ошибки: {type(e).__name__}")
        import traceback
        logger.error(f"SM_MAIN: Traceback: {traceback.format_exc()}")
        raise
