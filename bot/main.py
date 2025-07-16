import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from database.database import SessionLocal, init_db
from bot.dialog_manager import DialogManager
from bot.embedding import KnowledgeBaseManager
from config import settings

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
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
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
        
        keyboard = [
            [InlineKeyboardButton("📋 Услуги", callback_data="services")],
            [InlineKeyboardButton("👩‍💼 Мастера", callback_data="masters")],
            [InlineKeyboardButton("📅 Записаться", callback_data="booking")],
            [InlineKeyboardButton("❓ Задать вопрос", callback_data="question")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

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
        await update.message.reply_text(help_text)

    async def services_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /services"""
        with SessionLocal() as db:
            dialog_manager = DialogManager(db)
            services_text = await dialog_manager.youclients_api.format_services_list()
            
            keyboard = [
                [InlineKeyboardButton("📅 Записаться", callback_data="booking")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(services_text, reply_markup=reply_markup)

    async def masters_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /masters"""
        with SessionLocal() as db:
            dialog_manager = DialogManager(db)
            masters_text = await dialog_manager.youclients_api.format_masters_list()
            
            keyboard = [
                [InlineKeyboardButton("📅 Записаться", callback_data="booking")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(masters_text, reply_markup=reply_markup)

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /profile"""
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
            
            await update.message.reply_text(profile_text)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "services":
            await self.services_command(update, context)
        elif query.data == "masters":
            await self.masters_command(update, context)
        elif query.data == "booking":
            await query.edit_message_text(
                "📅 Для записи напишите что вас интересует, например:\n\n"
                "• 'Хочу записаться на маникюр'\n"
                "• 'Запиши меня к Наталье на завтра'\n"
                "• 'Нужен педикюр на пятницу вечером'"
            )
        elif query.data == "question":
            await query.edit_message_text(
                "❓ Задайте любой вопрос о салоне, например:\n\n"
                "• 'Сколько стоит маникюр?'\n"
                "• 'Где вы находитесь?'\n"
                "• 'Какие у вас есть услуги?'"
            )
        elif query.data == "start":
            await self.start_command(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            with SessionLocal() as db:
                dialog_manager = DialogManager(db)
                
                user_data = {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
                
                response = await dialog_manager.process_message(
                    str(user.id), 
                    user_data, 
                    message_text,
                    update.message.message_id
                )
                
                await update.message.reply_text(response)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего сообщения. "
                "Попробуйте еще раз или обратитесь к администратору."
            )

    async def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        
        # Инициализация базы данных
        init_db()
        
        # Загрузка базы знаний
        try:
            kb_manager = KnowledgeBaseManager()
            await kb_manager.load_knowledge_base()
            logger.info("База знаний загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке базы знаний: {e}")
        
        # Запуск бота
        await self.application.run_polling(drop_pending_updates=True)


async def main():
    """Главная функция"""
    bot = TelegramBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main()) 