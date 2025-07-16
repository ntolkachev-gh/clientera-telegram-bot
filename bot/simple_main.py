import asyncio
import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database.database import SessionLocal, init_db
from database.models import Client, Session as ChatSession, Message
from bot.openai_client import OpenAIClient
from config import settings

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
                
                messages = [
                    {
                        "role": "system",
                        "content": f"""Ты - дружелюбный помощник в салоне красоты. 
                        Общайся с клиентом {client.first_name or 'дорогой клиент'} тепло и профессионально.
                        Отвечай на вопросы о салоне, услугах, записи.
                        Если не знаешь точной информации, честно скажи об этом."""
                    },
                    {
                        "role": "user",
                        "content": message_text
                    }
                ]
                
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