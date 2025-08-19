#!/usr/bin/env python3
"""
Скрипт для создания услуг и мастеров в Youclients API
"""

import asyncio
import logging
from bot.youclients_api import YouclientsAPI
from config import settings

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def create_services():
    """Создание услуг в Youclients"""
    youclients_api = YouclientsAPI()
    
    # Список услуг для создания
    services = [
        {
            "title": "Массаж классический",
            "description": "Классический массаж всего тела для расслабления и снятия напряжения",
            "price": 3000,
            "duration": 60,
            "is_active": True
        },
        {
            "title": "Массаж расслабляющий",
            "description": "Расслабляющий массаж с использованием ароматических масел",
            "price": 3500,
            "duration": 60,
            "is_active": True
        },
        {
            "title": "Обертывание морскими водорослями",
            "description": "Обертывание морскими водорослями для детоксикации и улучшения состояния кожи",
            "price": 4000,
            "duration": 90,
            "is_active": True
        },
        {
            "title": "Обертывание шоколадное",
            "description": "Шоколадное обертывание для увлажнения и питания кожи",
            "price": 4500,
            "duration": 90,
            "is_active": True
        },
        {
            "title": "СПА-процедура",
            "description": "Комплексная СПА-процедура включающая массаж, обертывание и уход за лицом",
            "price": 6000,
            "duration": 120,
            "is_active": True
        },
        {
            "title": "Маникюр",
            "description": "Классический маникюр с покрытием гель-лаком",
            "price": 2000,
            "duration": 60,
            "is_active": True
        },
        {
            "title": "Педикюр",
            "description": "Классический педикюр с покрытием гель-лаком",
            "price": 2500,
            "duration": 90,
            "is_active": True
        }
    ]
    
    logger.info("Начинаем создание услуг...")
    
    for service_data in services:
        try:
            logger.info(f"Создаем услугу: {service_data['title']}")
            result = await youclients_api.create_service(service_data)
            
            if result.get("success"):
                logger.info(f"✅ Услуга '{service_data['title']}' успешно создана")
            else:
                logger.error(f"❌ Ошибка создания услуги '{service_data['title']}': {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Исключение при создании услуги '{service_data['title']}': {e}")
    
    logger.info("Создание услуг завершено")


async def create_masters():
    """Создание мастеров в Youclients"""
    youclients_api = YouclientsAPI()
    
    # Список мастеров для создания
    masters = [
        {
            "name": "Анна",
            "surname": "Петрова",
            "phone": "+7 (999) 123-45-67",
            "email": "anna.petrova@salon.ru",
            "specialization": "Массажист, СПА-терапевт",
            "is_active": True,
            "work_schedule": {
                "monday": {"start": "09:00", "end": "18:00"},
                "tuesday": {"start": "09:00", "end": "18:00"},
                "wednesday": {"start": "09:00", "end": "18:00"},
                "thursday": {"start": "09:00", "end": "18:00"},
                "friday": {"start": "09:00", "end": "18:00"},
                "saturday": {"start": "10:00", "end": "16:00"},
                "sunday": {"start": "10:00", "end": "16:00"}
            }
        },
        {
            "name": "Мария",
            "surname": "Иванова",
            "phone": "+7 (999) 234-56-78",
            "email": "maria.ivanova@salon.ru",
            "specialization": "Косметолог, мастер по обертываниям",
            "is_active": True,
            "work_schedule": {
                "monday": {"start": "10:00", "end": "19:00"},
                "tuesday": {"start": "10:00", "end": "19:00"},
                "wednesday": {"start": "10:00", "end": "19:00"},
                "thursday": {"start": "10:00", "end": "19:00"},
                "friday": {"start": "10:00", "end": "19:00"},
                "saturday": {"start": "11:00", "end": "17:00"},
                "sunday": {"start": "11:00", "end": "17:00"}
            }
        },
        {
            "name": "Елена",
            "surname": "Сидорова",
            "phone": "+7 (999) 345-67-89",
            "email": "elena.sidorova@salon.ru",
            "specialization": "Мастер маникюра и педикюра",
            "is_active": True,
            "work_schedule": {
                "monday": {"start": "09:00", "end": "18:00"},
                "tuesday": {"start": "09:00", "end": "18:00"},
                "wednesday": {"start": "09:00", "end": "18:00"},
                "thursday": {"start": "09:00", "end": "18:00"},
                "friday": {"start": "09:00", "end": "18:00"},
                "saturday": {"start": "10:00", "end": "16:00"},
                "sunday": {"start": "10:00", "end": "16:00"}
            }
        }
    ]
    
    logger.info("Начинаем создание мастеров...")
    
    for master_data in masters:
        try:
            full_name = f"{master_data['name']} {master_data['surname']}"
            logger.info(f"Создаем мастера: {full_name}")
            result = await youclients_api.create_master(master_data)
            
            if result.get("success"):
                logger.info(f"✅ Мастер '{full_name}' успешно создан")
            else:
                logger.error(f"❌ Ошибка создания мастера '{full_name}': {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Исключение при создании мастера '{full_name}': {e}")
    
    logger.info("Создание мастеров завершено")


async def list_existing():
    """Показать существующие услуги и мастеров"""
    youclients_api = YouclientsAPI()
    
    logger.info("Получаем список существующих услуг...")
    services = await youclients_api.get_services()
    logger.info(f"Найдено услуг: {len(services)}")
    for service in services:
        logger.info(f"  - {service.get('title', 'Без названия')} (ID: {service.get('id', 'N/A')})")
    
    logger.info("Получаем список существующих мастеров...")
    masters = await youclients_api.get_masters()
    logger.info(f"Найдено мастеров: {len(masters)}")
    for master in masters:
        name = f"{master.get('name', '')} {master.get('surname', '')}"
        logger.info(f"  - {name} (ID: {master.get('id', 'N/A')})")


async def main():
    """Главная функция"""
    logger.info("=== Скрипт настройки Youclients ===")
    
    # Показываем существующие данные
    await list_existing()
    
    print("\n" + "="*50)
    print("Выберите действие:")
    print("1. Создать услуги")
    print("2. Создать мастеров")
    print("3. Создать услуги и мастеров")
    print("4. Только показать существующие")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        await create_services()
    elif choice == "2":
        await create_masters()
    elif choice == "3":
        await create_services()
        await create_masters()
    elif choice == "4":
        logger.info("Показываем только существующие данные")
    else:
        logger.error("Неверный выбор")
        return
    
    logger.info("=== Завершено ===")


if __name__ == "__main__":
    asyncio.run(main()) 