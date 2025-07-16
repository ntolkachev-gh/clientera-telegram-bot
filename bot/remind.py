import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from telegram import Bot
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Client, Appointment
from config import settings

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ReminderSystem:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.db = SessionLocal()

    async def get_clients_for_reminder(self) -> List[Client]:
        """Получение клиентов, которым нужно отправить напоминание"""
        today = datetime.now().date()
        
        # Получаем клиентов, которые давно не были в салоне
        clients = self.db.query(Client).filter(
            Client.last_visit_date.isnot(None)
        ).all()
        
        clients_to_remind = []
        
        for client in clients:
            if client.last_visit_date:
                days_since_visit = (today - client.last_visit_date.date()).days
                remind_after = client.remind_after_days or settings.remind_after_days
                
                if days_since_visit >= remind_after:
                    clients_to_remind.append(client)
        
        return clients_to_remind

    async def send_reminder(self, client: Client) -> bool:
        """Отправка напоминания клиенту"""
        try:
            # Персонализированное сообщение на основе предпочтений
            favorite_services = client.favorite_services or []
            favorite_masters = client.favorite_masters or []
            
            message = f"👋 Привет, {client.first_name or 'дорогой клиент'}!\n\n"
            
            if client.last_visit_date:
                days_ago = (datetime.now().date() - client.last_visit_date.date()).days
                message += f"Прошло уже {days_ago} дней с вашего последнего визита к нам.\n"
            
            message += "Время позаботиться о себе! 💅✨\n\n"
            
            # Персонализированные предложения
            if favorite_services:
                service_text = ", ".join(favorite_services[:2])
                message += f"Может быть, пора записаться на {service_text}?\n"
            
            if favorite_masters:
                master_text = ", ".join(favorite_masters[:2])
                message += f"Ваши любимые мастера {master_text} будут рады вас видеть!\n"
            
            message += "\n📅 Напишите мне, чтобы записаться на удобное время.\n"
            message += "Или просто скажите /start для выбора услуги."
            
            await self.bot.send_message(
                chat_id=client.telegram_id,
                text=message
            )
            
            logger.info(f"Напоминание отправлено клиенту {client.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания клиенту {client.telegram_id}: {e}")
            return False

    async def send_appointment_reminder(self, appointment: Appointment) -> bool:
        """Отправка напоминания о записи"""
        try:
            client = appointment.client
            appointment_time = appointment.appointment_datetime
            
            # Напоминание за день до записи
            tomorrow = datetime.now() + timedelta(days=1)
            if appointment_time.date() == tomorrow.date():
                message = f"📅 Напоминание о записи!\n\n"
                message += f"Завтра {appointment_time.strftime('%d.%m.%Y')} в {appointment_time.strftime('%H:%M')}\n"
                message += f"Услуга: {appointment.service_name}\n"
                message += f"Мастер: {appointment.master_name}\n\n"
                message += "Ждем вас в салоне! 😊\n"
                message += "Если планы изменились, сообщите нам заранее."
                
                await self.bot.send_message(
                    chat_id=client.telegram_id,
                    text=message
                )
                
                logger.info(f"Напоминание о записи отправлено клиенту {client.telegram_id}")
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания о записи: {e}")
            return False

    async def run_reminder_job(self):
        """Основная задача для отправки напоминаний"""
        logger.info("Запуск задачи напоминаний...")
        
        try:
            # Отправляем напоминания о повторной записи
            clients_to_remind = await self.get_clients_for_reminder()
            
            logger.info(f"Найдено {len(clients_to_remind)} клиентов для напоминания")
            
            success_count = 0
            for client in clients_to_remind:
                if await self.send_reminder(client):
                    success_count += 1
                    
                    # Обновляем дату последнего напоминания
                    # (можно добавить поле last_reminder_date в модель Client)
                    
                # Небольшая задержка между отправками
                await asyncio.sleep(1)
            
            logger.info(f"Отправлено {success_count} напоминаний о повторной записи")
            
            # Отправляем напоминания о предстоящих записях
            upcoming_appointments = self.db.query(Appointment).filter(
                Appointment.appointment_datetime >= datetime.now(),
                Appointment.appointment_datetime <= datetime.now() + timedelta(days=1),
                Appointment.status == "scheduled"
            ).all()
            
            appointment_reminders = 0
            for appointment in upcoming_appointments:
                if await self.send_appointment_reminder(appointment):
                    appointment_reminders += 1
                await asyncio.sleep(1)
            
            logger.info(f"Отправлено {appointment_reminders} напоминаний о записях")
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении задачи напоминаний: {e}")
        
        finally:
            self.db.close()

    async def send_promotional_message(self, message_text: str, target_clients: Optional[List[Client]] = None):
        """Отправка промо-сообщений"""
        if target_clients is None:
            # Отправляем всем активным клиентам
            target_clients = self.db.query(Client).filter(
                Client.created_at >= datetime.now() - timedelta(days=90)
            ).all()
        
        if target_clients:
            logger.info(f"Отправка промо-сообщения {len(target_clients)} клиентам")
            
            success_count = 0
            for client in target_clients:
                try:
                    await self.bot.send_message(
                        chat_id=client.telegram_id,
                        text=message_text
                    )
                    success_count += 1
                    await asyncio.sleep(0.5)  # Меньшая задержка для промо
                    
                except Exception as e:
                    logger.error(f"Ошибка при отправке промо клиенту {client.telegram_id}: {e}")
            
            logger.info(f"Промо-сообщение отправлено {success_count} клиентам")

    async def cleanup_old_sessions(self):
        """Очистка старых неактивных сессий"""
        from database.models import Session as ChatSession
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        old_sessions = self.db.query(ChatSession).filter(
            ChatSession.session_end < cutoff_date,
            ChatSession.is_active == False
        ).all()
        
        for session in old_sessions:
            self.db.delete(session)
        
        self.db.commit()
        logger.info(f"Удалено {len(old_sessions)} старых сессий")


async def main():
    """Главная функция для запуска напоминаний"""
    reminder_system = ReminderSystem()
    await reminder_system.run_reminder_job()


if __name__ == "__main__":
    asyncio.run(main()) 