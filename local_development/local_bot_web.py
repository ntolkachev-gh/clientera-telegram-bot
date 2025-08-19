#!/usr/bin/env python3
"""
Локальный веб-интерфейс для имитации работы Telegram бота
"""

import sys
import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit

# Настройка логирования для вывода в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Явно указываем stdout для консоли
    ]
)
logger = logging.getLogger(__name__)

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal, init_db
from database.models import Client, Session as ChatSession, Message
from core.openai_client import OpenAIClient
from bot.embedding import KnowledgeBaseManager
from config import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local_bot_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Настройка логирования Flask
app.logger.setLevel(logging.INFO)
app.logger.handlers.clear()
app.logger.addHandler(logging.StreamHandler(sys.stdout))

# Настройка логирования Werkzeug (веб-сервер Flask)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
werkzeug_logger.handlers.clear()
werkzeug_logger.addHandler(logging.StreamHandler(sys.stdout))

class LocalBot:
    def __init__(self):
        self.kb_manager = KnowledgeBaseManager()

    def get_or_create_client(self, user_id: str, user_data: dict):
        """Получение или создание клиента"""
        with SessionLocal() as db:
            client = db.query(Client).filter(Client.telegram_id == user_id).first()

            if not client:
                client = Client(
                    telegram_id=user_id,
                    username=user_data.get("username"),
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name")
                )
                db.add(client)
                db.commit()
                db.refresh(client)

            return client

    async def process_message(self, user_id: str, user_data: dict, message_text: str) -> str:
        """Обработка сообщения пользователя"""
        logger.info(f"🔄 Обработка сообщения от пользователя {user_id}: {message_text}")
        try:
            client = self.get_or_create_client(user_id, user_data)
            logger.info(f"👤 Клиент: {client.first_name} (ID: {client.id})")

            with SessionLocal() as db:
                # Создаем сессию
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
                    content=message_text
                )
                db.add(user_message)
                db.commit()

                # Получаем OpenAI клиент с поддержкой tools
                from core.yclients_client import YclientsClient
                yclients_client = YclientsClient(settings.youclients_api_key, settings.youclients_company_id)
                openai_client = OpenAIClient(db, yclients_client)

                # Получаем последние сообщения для контекста
                recent_messages = db.query(Message).filter(
                    Message.client_id == client.id
                ).order_by(Message.created_at.desc()).limit(10).all()

                # Формируем системный промпт
                system_prompt = (
                    "Ты — дружелюбный и профессиональный ассистент салона красоты.\n\n"
                    "Правила ответа:\n"
                    "1. Используй эмодзи, чтобы выделять ключевые моменты (но не перегружай).\n"
                    "2. Структурируй ответ: короткие абзацы, списки через •.\n"
                    "3. Если предлагаешь варианты даты/времени или услуг — выводи их на отдельных строках.\n"
                    "4. Всегда отвечай на русском.\n"
                    "5. Если нужна дополнительная информация для записи — чётко перечисли, что ещё уточнить.\n\n"
                    "Контекст о клиенте:\n"
                    f"• Имя клиента: {client.first_name or 'Неизвестно'}\n"
                    f"• Любимые услуги: {', '.join(getattr(client, 'favorite_services', []) or []) or 'нет данных'}\n"
                    f"• Любимые мастера: {', '.join(getattr(client, 'favorite_masters', []) or []) or 'нет данных'}\n"
                    f"• Предпочитаемое время: {', '.join(getattr(client, 'preferred_time_slots', []) or []) or 'нет данных'}\n\n"
                    "Всегда будь приветлив и помогай клиенту оформить запись или найти информацию."
                )

                # Формируем сообщения для GPT
                messages = [{"role": "system", "content": system_prompt}]

                for msg in reversed(recent_messages):
                    if hasattr(msg, 'message_type') and hasattr(msg, 'content') and isinstance(msg.content, str):
                        if msg.message_type == "user":
                            messages.append({"role": "user", "content": msg.content})
                        elif msg.message_type == "bot":
                            messages.append({"role": "assistant", "content": msg.content})

                messages.append({"role": "user", "content": message_text})

                # Получаем ответ от GPT
                logger.info("🤖 Отправка запроса в OpenAI...")
                response = await openai_client.chat_completion_with_tools(messages, client.id)
                logger.info(f"✅ Получен ответ от OpenAI: {response[:100]}...")

                # Сохраняем ответ бота
                bot_message = Message(
                    client_id=client.id,
                    session_id=session.id,
                    message_type="bot",
                    content=response
                )
                db.add(bot_message)
                db.commit()
                logger.info("💾 Ответ сохранен в базу данных")

                return response

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке сообщения: {e}")
            return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."

# Создаем экземпляр бота
bot = LocalBot()

@app.route('/')
def index():
    """Главная страница"""
    return render_template('local_bot.html')

@app.route('/api/send_message', methods=['POST'])
def send_message():
    """API для отправки сообщения"""
    logger.info("📨 Получен запрос на отправку сообщения")
    try:
        data = request.get_json()
        message_text = data.get('message', '')
        user_id = data.get('user_id', 'local_user_1')
        user_data = {
            "username": "local_user",
            "first_name": "Тестовый",
            "last_name": "Пользователь"
        }

        logger.info(f"📝 Сообщение: {message_text}")

        # Обрабатываем сообщение
        import asyncio
        response = asyncio.run(bot.process_message(user_id, user_data, message_text))

        logger.info("✅ Сообщение успешно обработано")
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Ошибка в API send_message: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search_knowledge', methods=['POST'])
def search_knowledge():
    """API для поиска в базе знаний"""
    logger.info("🔍 Получен запрос на поиск в базе знаний")
    try:
        data = request.get_json()
        query = data.get('query', '')

        logger.info(f"🔎 Запрос поиска: {query}")

        # Поиск в базе знаний
        import asyncio
        results = asyncio.run(bot.kb_manager.search_knowledge_base(query, limit=5))

        logger.info(f"📊 Найдено результатов: {len(results)}")
        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        logger.error(f"❌ Ошибка в API search_knowledge: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    import argparse

    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description='Локальный веб-интерфейс для бота')
    parser.add_argument('--port', type=int, default=8081, help='Порт для запуска (по умолчанию: 8081)')
    args = parser.parse_args()

    # Инициализируем базу данных
    logger.info("🗄️ Инициализация базы данных...")
    init_db()
    logger.info("✅ База данных инициализирована")

    logger.info("🚀 Запуск локального веб-интерфейса бота...")
    logger.info(f"📱 Откройте http://localhost:{args.port} в браузере")
    logger.info("🔄 Запуск сервера...")

    # Отключаем debug режим для более чистого вывода логов
    socketio.run(app, host='0.0.0.0', port=args.port, debug=False, log_output=True)
