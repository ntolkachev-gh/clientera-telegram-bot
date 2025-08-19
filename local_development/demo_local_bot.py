#!/usr/bin/env python3
"""
Демо-версия локального бота для тестирования
Работает без внешних API и базы данных
"""

from flask import Flask, render_template, request, jsonify, session
import uuid
import json
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'demo_local_bot_secret_key'

# Демо-данные
DEMO_SERVICES = [
    "💅 Маникюр - от 1500₽",
    "🦶 Педикюр - от 2000₽",
    "💇‍♀️ Стрижка - от 2500₽",
    "🎨 Окрашивание волос - от 5000₽",
    "🧖‍♀️ Массаж - от 3000₽",
    "💆‍♀️ Маска для лица - от 2000₽"
]

DEMO_MASTERS = [
    "👩‍💼 Наталья - мастер по маникюру и педикюру",
    "👩‍💼 Елена - парикмахер-стилист",
    "👩‍💼 Мария - косметолог",
    "👩‍💼 Анна - массажист"
]

DEMO_SALON_INFO = {
    "address": "ул. Красивая, 123, Москва",
    "phone": "+7 (495) 123-45-67",
    "working_hours": "Пн-Вс: 9:00-21:00",
    "instagram": "@beauty_salon_moscow"
}

# История чата
chat_history = {}

class DemoBot:
    def __init__(self):
        self.name = "Демо-бот салона красоты"
        self.responses = {
            "привет": "👋 Привет! Я демо-версия бота салона красоты. Чем могу помочь?",
            "услуги": "📋 Наши услуги:\n" + "\n".join(DEMO_SERVICES),
            "мастера": "👩‍💼 Наши мастера:\n" + "\n".join(DEMO_MASTERS),
            "адрес": f"📍 Адрес: {DEMO_SALON_INFO['address']}",
            "телефон": f"📞 Телефон: {DEMO_SALON_INFO['phone']}",
            "время": f"🕐 Время работы: {DEMO_SALON_INFO['working_hours']}",
            "цены": "💰 Цены на услуги:\n" + "\n".join(DEMO_SERVICES),
            "записаться": "📅 Для записи на услугу, укажите:\n• Какую услугу хотите\n• Предпочтительную дату и время\n• К какому мастеру (если есть предпочтения)",
            "помощь": """🤖 Как я могу помочь:

📋 Информация:
• "услуги" - список услуг и цены
• "мастера" - наши специалисты
• "адрес" - где мы находимся
• "телефон" - контакты
• "время" - график работы

📅 Запись:
• "записаться" - инструкции по записи
• "хочу маникюр" - запись на конкретную услугу

💬 Просто напишите, что вас интересует!"""
        }

    def get_response(self, message):
        """Получает ответ на сообщение пользователя"""
        message_lower = message.lower()

        # Проверяем ключевые слова
        for key, response in self.responses.items():
            if key in message_lower:
                return response

        # Специальные случаи
        if "маникюр" in message_lower or "педикюр" in message_lower:
            return f"💅 Отлично! Вы хотите записаться на {message}. Укажите желаемую дату и время, например: 'завтра в 15:00'"

        if "стрижка" in message_lower or "окрашивание" in message_lower:
            return f"💇‍♀️ Хороший выбор! Для записи на {message} укажите удобную дату и время."

        if "завтра" in message_lower or "сегодня" in message_lower:
            return "📅 Отлично! Для подтверждения записи позвоните нам по телефону +7 (495) 123-45-67 или оставьте заявку на сайте."

        if "сколько стоит" in message_lower:
            return "💰 Цены на услуги:\n" + "\n".join(DEMO_SERVICES) + "\n\n💡 Для точной стоимости конкретной услуги уточните детали!"

        if "спасибо" in message_lower or "благодарю" in message_lower:
            return "😊 Рада была помочь! Если у вас есть еще вопросы, обращайтесь! 💕"

        # Общий ответ
        return """🤔 Не совсем понимаю ваш вопрос.

Попробуйте спросить:
• "услуги" - что мы предлагаем
• "мастера" - кто у нас работает
• "записаться" - как записаться
• "помощь" - полная справка

Или просто опишите, что вас интересует! 😊"""

# Создаем экземпляр демо-бота
demo_bot = DemoBot()

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
        username = session.get('username', 'demo_user')

        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400

        # Добавляем сообщение пользователя в историю
        if user_id not in chat_history:
            chat_history[user_id] = []

        chat_history[user_id].append({
            'type': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

        # Получаем ответ от демо-бота
        response = demo_bot.get_response(message)

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
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/services')
def get_services():
    """API для получения списка услуг"""
    return jsonify({'services': "\n".join(DEMO_SERVICES)})

@app.route('/api/masters')
def get_masters():
    """API для получения списка мастеров"""
    return jsonify({'masters': "\n".join(DEMO_MASTERS)})

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

@app.route('/api/status')
def get_status():
    """API для проверки статуса бота"""
    return jsonify({
        'status': 'online',
        'bot_name': demo_bot.name,
        'timestamp': datetime.now().isoformat(),
        'message': 'Демо-бот работает в тестовом режиме'
    })

if __name__ == '__main__':
    print("🚀 Демо-версия локального бота запущена!")
    print("📱 Откройте http://localhost:5001 в браузере")
    print("💬 Теперь вы можете тестировать демо-бота локально!")
    print("⚠️ Это демо-версия без реальных API и базы данных")
    print("🔧 Для полной версии настройте .env файл")

    app.run(debug=True, host='0.0.0.0', port=5001)
