import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database.database import SessionLocal, init_db
from bot.dialog_manager import DialogManager
from bot.embedding import KnowledgeBaseManager
from config import settings
import nest_asyncio

# Применяем nest_asyncio для решения проблем с event loop
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("services", self.services_command))
        self.application.add_handler(CommandHandler("masters", self.masters_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def _get_target_message(self, update: Update):
        """Пытается получить объект Message, чтобы можно было отправить ответ как из обычного сообщения, так и из callback_query"""
        if update.message:
            return update.message
        if update.callback_query and update.callback_query.message:
            return update.callback_query.message
        return None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start. Теперь без inline-кнопок."""
        user = update.effective_user
        welcome_message = f"""
👋 Добро пожаловать в салон красоты, {user.first_name}!

Я помогу вам:
• 📅 Записаться на услуги
• 💬 Ответить на вопросы о салоне
• 👩‍💼 Выбрать подходящего мастера
• ⏰ Найти удобное время

Просто напишите что вас интересует, например:
"Хочу записаться на маникюр к Наталье на завтра"

Или воспользуйтесь командами:
/services - список услуг
/masters - наши мастера
/profile - ваш профиль
/help - помощь
        """
        if update.message:
            await update.message.reply_text(welcome_message)
        else:
            chat_id = update.effective_chat.id if update.effective_chat else None
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """
🤖 Как пользоваться ботом:

📝 **Запись на услуги:**
• "Хочу записаться на маникюр"
• "Запиши меня к Наталье на завтра в 15:00"
• "Нужен педикюр на пятницу"

❓ **Вопросы о салоне:**
• "Сколько стоит маникюр?"
• "Какие у вас есть услуги?"
• "Где находится салон?"

👤 **Профиль:**
• /profile - посмотреть свой профиль
• Бот запоминает ваши предпочтения

📞 **Команды:**
• /start - главное меню
• /services - список услуг
• /masters - наши мастера
• /help - эта справка

Просто пишите естественным языком, я пойму! 😊
        """
        if update.message:
            await update.message.reply_text(help_text)
        else:
            chat_id = update.effective_chat.id if update.effective_chat else None
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=help_text)

    async def services_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /services – теперь без inline-кнопок"""
        with SessionLocal() as db:
            dialog_manager = DialogManager(db)
            services_text = await dialog_manager.youclients_api.format_services_list()
            if update.message:
                await update.message.reply_text(services_text)
            else:
                chat_id = update.effective_chat.id if update.effective_chat else None
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=services_text)

    async def masters_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /masters – теперь без inline-кнопок"""
        with SessionLocal() as db:
            dialog_manager = DialogManager(db)
            masters_text = await dialog_manager.youclients_api.format_masters_list()
            if update.message:
                await update.message.reply_text(masters_text)
            else:
                chat_id = update.effective_chat.id if update.effective_chat else None
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=masters_text)

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /profile – теперь без inline-кнопок"""
        user = update.effective_user
        with SessionLocal() as db:
            dialog_manager = DialogManager(db)
            client = dialog_manager.get_or_create_client(str(user.id), {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            })
            stats = dialog_manager.get_client_stats(client.id)
            profile_text = f"""
👤 **Ваш профиль:**

📱 Имя: {stats.get('name', 'Не указано')}
💬 Сообщений: {stats.get('messages_count', 0)}
🔄 Сессий: {stats.get('sessions_count', 0)}
📅 Регистрация: {stats.get('created_at', '').strftime('%d.%m.%Y') if stats.get('created_at') else 'Не указано'}

❤️ **Предпочтения:**
• Услуги: {', '.join(stats.get('favorite_services', [])) or 'Не указано'}
• Мастера: {', '.join(stats.get('favorite_masters', [])) or 'Не указано'}
• Время: {', '.join(stats.get('preferred_time_slots', [])) or 'Не указано'}

🗓️ Последний визит: {stats.get('last_visit', 'Не указано')}
            """
            if update.message:
                await update.message.reply_text(profile_text)
            else:
                chat_id = update.effective_chat.id if update.effective_chat else None
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=profile_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user = update.effective_user if update.effective_user else None
        message_text = update.message.text if update.message else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        # Показываем, что бот печатает
        if chat_id is not None:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        # Если нет текста сообщения или пользователя — не обрабатывать
        if not user or not message_text:
            return
        try:
            with SessionLocal() as db:
                dialog_manager = DialogManager(db)
                user_data = {
                    "username": getattr(user, "username", None),
                    "first_name": getattr(user, "first_name", None),
                    "last_name": getattr(user, "last_name", None)
                }
                response = await dialog_manager.process_message(
                    str(user.id),
                    user_data,
                    message_text,
                    update.message.message_id if update.message else None
                )
                if update.message:
                    await update.message.reply_text(response)
                elif chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=response)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            error_text = "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз или обратитесь к администратору."
            if update.message:
                await update.message.reply_text(error_text)
            elif chat_id:
                await context.bot.send_message(chat_id=chat_id, text=error_text)

    async def run(self):
        """Синхронный запуск бота (без запуска дополнительного цикла asyncio)."""
        logger.info("Запуск Telegram бота...")

        # Инициализация базы данных
        init_db()

        # База знаний уже загружена в Qdrant, пропускаем повторную загрузку
        logger.info("База знаний уже загружена в Qdrant")

        # Проверяем, что коллекция существует
        try:
            kb_manager = KnowledgeBaseManager()
            collections = kb_manager.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == kb_manager.collection_name
                for collection in collections.collections
            )
            if collection_exists:
                logger.info(f"Коллекция {kb_manager.collection_name} найдена в Qdrant")
            else:
                logger.warning(f"Коллекция {kb_manager.collection_name} не найдена в Qdrant")
        except Exception as e:
            logger.error(f"Ошибка при проверке базы знаний: {e}")

                        # Запускаем polling
        logger.info("Запуск polling...")
        await self.application.run_polling(drop_pending_updates=True)


async def main():
    """Точка входа"""
    bot = TelegramBot()
    await bot.run()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise
