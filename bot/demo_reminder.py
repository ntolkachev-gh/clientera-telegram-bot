import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Client
from config import settings

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class DemoReminderSystem:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.db = SessionLocal()
        
        # Шаблоны сообщений для демо
        self.demo_messages = [
            {
                "text": "💅 Привет! Не забудьте о себе! У нас сегодня отличные предложения на маникюр и педикюр. Хотите записаться?",
                "services": ["маникюр", "педикюр"]
            },
            {
                "text": "✨ Красота требует внимания! Запишитесь на стрижку или окрашивание. Наши мастера ждут вас!",
                "services": ["стрижка", "окрашивание"]
            },
            {
                "text": "🌸 Время обновить образ! У нас есть свободное время для укладки и макияжа. Запишитесь прямо сейчас!",
                "services": ["укладка", "макияж"]
            },
            {
                "text": "💆‍♀️ Расслабьтесь и отдохните! Массаж лица и SPA-процедуры помогут восстановить силы. Запишитесь на удобное время!",
                "services": ["массаж лица", "SPA"]
            },
            {
                "text": "🎨 Хотите изменить цвет волос? Наши стилисты помогут подобрать идеальный оттенок. Запишитесь на консультацию!",
                "services": ["окрашивание", "консультация стилиста"]
            },
            {
                "text": "💇‍♀️ Новая стрижка - новое настроение! У нас есть время для стрижки и укладки. Запишитесь прямо сейчас!",
                "services": ["стрижка", "укладка"]
            },
            {
                "text": "💅 Идеальный маникюр за 60 минут! У нас есть свободное время. Запишитесь и получите скидку 10%!",
                "services": ["маникюр"]
            },
            {
                "text": "✨ Специальное предложение! Запишитесь на любую услугу сегодня и получите бесплатную консультацию!",
                "services": ["любая услуга"]
            }
        ]

    async def get_active_clients(self) -> List[Client]:
        """Получение активных клиентов для демо"""
        # Получаем клиентов, которые были активны в последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        clients = self.db.query(Client).filter(
            Client.created_at >= thirty_days_ago
        ).all()
        
        # Если клиентов мало, берем всех
        if len(clients) < 5:
            clients = self.db.query(Client).all()
        
        return clients

    async def send_demo_reminder(self, client: Client) -> bool:
        """Отправка демо-напоминания клиенту без inline-кнопок"""
        try:
            # Выбираем случайное сообщение
            message_template = random.choice(self.demo_messages)
            # Персонализируем сообщение
            client_name = client.first_name or "дорогой клиент"
            personalized_text = message_template["text"].replace("Привет!", f"Привет, {client_name}!")
            # Добавляем призыв к действию
            call_to_action = "\n\n💬 Напишите мне, чтобы записаться на удобное время!"
            full_message = personalized_text + call_to_action
            await self.bot.send_message(
                chat_id=client.telegram_id,
                text=full_message
            )
            logger.info(f"Демо-напоминание отправлено клиенту {client.telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке демо-напоминания клиенту {client.telegram_id}: {e}")
            return False

    async def send_demo_reminders_batch(self):
        """Отправка демо-напоминаний партией"""
        logger.info("Отправка демо-напоминаний...")
        
        try:
            clients = await self.get_active_clients()
            
            if not clients:
                logger.warning("Нет клиентов для отправки демо-напоминаний")
                return
            
            # Выбираем случайных клиентов (не более 10 за раз)
            selected_clients = random.sample(clients, min(len(clients), 10))
            
            logger.info(f"Отправка демо-напоминаний {len(selected_clients)} клиентам")
            
            success_count = 0
            for client in selected_clients:
                if await self.send_demo_reminder(client):
                    success_count += 1
                
                # Задержка между отправками (1-3 секунды)
                await asyncio.sleep(random.uniform(1, 3))
            
            logger.info(f"Отправлено {success_count} демо-напоминаний")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке демо-напоминаний: {e}")

    async def run_demo_loop(self, interval_minutes: int = 15):
        """Запуск цикла демо-напоминаний"""
        logger.info(f"Запуск демо-цикла с интервалом {interval_minutes} минут")
        
        while True:
            try:
                await self.send_demo_reminders_batch()
                
                # Ждем указанный интервал
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Демо-цикл остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в демо-цикле: {e}")
                # Ждем 5 минут перед повторной попыткой
                await asyncio.sleep(300)
        
        self.db.close()


async def main():
    """Главная функция для запуска демо-напоминаний"""
    demo_system = DemoReminderSystem()
    
    # Запускаем цикл с интервалом 15 минут
    await demo_system.run_demo_loop(interval_minutes=15)


if __name__ == "__main__":
    asyncio.run(main()) 