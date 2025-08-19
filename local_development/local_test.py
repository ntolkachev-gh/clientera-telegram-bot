import asyncio
import logging
from flask import Flask, render_template, request, jsonify, session
from database.database import SessionLocal, init_db
from bot.dialog_manager import DialogManager
from bot.embedding import KnowledgeBaseManager
from config import settings
import uuid
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'local_test_secret_key'

# Глобальные переменные для хранения состояния
kb_manager = None
chat_history = {}

class LocalBot:
    def __init__(self):
        self.kb_manager = None
        self.init_complete = False

    async def initialize(self):
        """Инициализация бота"""
        try:
            # Инициализация базы данных
            init_db()

            # Загрузка базы знаний
            self.kb_manager = KnowledgeBaseManager()
            await self.kb_manager.load_knowledge_base()
            logger.info("База знаний загружена")

            self.init_complete = True
            logger.info("Локальный бот инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {e}")
            raise

    async def process_message(self, user_id: str, message: str, username: str = "test_user"):
        """Обработка сообщения пользователя"""
        if not self.init_complete:
            return "Бот еще инициализируется, подождите немного..."

        try:
            with SessionLocal() as db:
                dialog_manager = DialogManager(db)
                user_data = {
                    "username": username,
                    "first_name": username,
                    "last_name": ""
                }

                response = await dialog_manager.process_message(
                    user_id,
                    user_data,
                    message,
                    int(datetime.now().timestamp())
                )
                return response
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            return f"Извините, произошла ошибка: {str(e)}"

    async def get_services(self):
        """Получение списка услуг"""
        if not self.init_complete:
            return "Бот еще инициализируется, подождите немного..."

        try:
            with SessionLocal() as db:
                dialog_manager = DialogManager(db)
                return await dialog_manager.youclients_api.format_services_list()
        except Exception as e:
            logger.error(f"Ошибка при получении услуг: {e}")
            return f"Ошибка при получении услуг: {str(e)}"

    async def get_masters(self):
        """Получение списка мастеров"""
        if not self.init_complete:
            return "Бот еще инициализируется, подождите немного..."

        try:
            with SessionLocal() as db:
                dialog_manager = DialogManager(db)
                return await dialog_manager.youclients_api.format_masters_list()
        except Exception as e:
            logger.error(f"Ошибка при получении мастеров: {e}")
            return f"Ошибка при получении мастеров: {str(e)}"

# Создаем экземпляр бота
local_bot = LocalBot()

@app.route('/')
def index():
    """Главная страница чата"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['username'] = f"user_{session['user_id'][:8]}"

    return render_template('chat.html', username=session['username'])

@app.route('/api/chat', methods=['POST'])
def chat():
    """API для отправки сообщений"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        user_id = session.get('user_id', str(uuid.uuid4()))
        username = session.get('username', 'test_user')

        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400

        # Добавляем сообщение в историю
        if user_id not in chat_history:
            chat_history[user_id] = []

        chat_history[user_id].append({
            'type': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

        # Обрабатываем сообщение через бота
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(local_bot.process_message(user_id, message, username))
        finally:
            loop.close()

        # Добавляем ответ бота в историю
        chat_history[user_id].append({
            'type': 'bot',
            'message': response,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'response': response,
            'user_id': user_id
        })

    except Exception as e:
        logger.error(f"Ошибка в API чата: {e}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/services')
def get_services():
    """API для получения списка услуг"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            services = loop.run_until_complete(local_bot.get_services())
        finally:
            loop.close()

        return jsonify({'services': services})

    except Exception as e:
        logger.error(f"Ошибка при получении услуг: {e}")
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/masters')
def get_masters():
    """API для получения списка мастеров"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            masters = loop.run_until_complete(local_bot.get_masters())
        finally:
            loop.close()

        return jsonify({'masters': masters})

    except Exception as e:
        logger.error(f"Ошибка при получении мастеров: {e}")
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/chat_history')
def get_chat_history():
    """API для получения истории чата"""
    user_id = session.get('user_id')
    if user_id and user_id in chat_history:
        return jsonify({'history': chat_history[user_id]})
    return jsonify({'history': []})

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """API для очистки истории чата"""
    user_id = session.get('user_id')
    if user_id and user_id in chat_history:
        chat_history[user_id] = []
    return jsonify({'success': True})

if __name__ == '__main__':
    # Инициализируем бота при запуске
    async def init_bot():
        await local_bot.initialize()

    # Запускаем инициализацию
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init_bot())
    finally:
        loop.close()

    print("🚀 Локальный бот запущен!")
    print("📱 Откройте http://localhost:5000 в браузере")
    print("💬 Теперь вы можете тестировать бота локально!")

    app.run(debug=True, host='0.0.0.0', port=5001)
