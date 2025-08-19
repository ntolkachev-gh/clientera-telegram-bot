#!/usr/bin/env python3
"""
Простая версия Telegram бота для тестирования
"""

import sys
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleBot:
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
👋 Привет, {user.first_name}!

Я простой тестовый бот салона красоты.

Команды:
/start - это сообщение
/help - справка

Просто напишите что-нибудь, и я отвечу!
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """
🤖 Справка по боту:

Это тестовая версия бота салона красоты.

Просто пишите сообщения, и я буду отвечать!
        """
        await update.message.reply_text(help_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        message_text = update.message.text
        user = update.effective_user

        response = f"""
💬 Вы написали: "{message_text}"

👤 Ваше имя: {user.first_name or 'Не указано'}
🆔 Ваш ID: {user.id}

Это тестовая версия бота. В полной версии здесь будет обработка запросов о салоне красоты!
        """

        await update.message.reply_text(response)

    async def run(self):
        """Запуск бота"""
        logger.info("Запуск простого Telegram бота...")
        await self.application.run_polling(drop_pending_updates=True)

async def main():
    """Точка входа"""
    bot = SimpleBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        raise
