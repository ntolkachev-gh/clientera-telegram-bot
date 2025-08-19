#!/usr/bin/env python3
"""
Финальное обновление базы знаний из YClients API с исправленными настройками
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.yclients_client import YclientsClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_knowledge_base_final():
    """Финальное обновление базы знаний с реальными данными API"""

    print("=" * 70)
    print("🎯 ФИНАЛЬНОЕ ОБНОВЛЕНИЕ БАЗЫ ЗНАНИЙ YCLIENTS API")
    print("=" * 70)

    # Используем реальные данные
    company_id = "1297379"
    api_key = "nmnsgmfcpdu65db2b5kp"

    print(f"🔑 Company ID: {company_id}")
    print(f"🔐 API Key: {api_key[:10]}...")
    print()

    # Инициализируем клиент
    yclients = YclientsClient(api_key=api_key, company_id=company_id)

    try:
        # Получаем реальные данные с принудительным обновлением
        print("🔄 Получаем услуги из API (с очисткой кэша)...")
        yclients.clear_cache()  # Очищаем кэш
        services = await yclients.get_services(force_refresh=True, use_real_api=True)

        print("🔄 Получаем сотрудников из API...")
        staff_list = await yclients.get_staff(force_refresh=True, use_real_api=True)

        print(f"✅ Получено {len(services)} услуг и {len(staff_list)} сотрудников")

        if len(services) > 10:  # Проверяем, что получили реальные данные
            print("🎉 Получены реальные данные из API!")

            # Генерируем обновленный файл услуг
            services_content = generate_real_services_md(services, staff_list)

            # Сохраняем файл
            services_file = "knowledge_base/salon_services_real.md"
            with open(services_file, 'w', encoding='utf-8') as f:
                f.write(services_content)

            print(f"✅ Файл реальных услуг создан: {services_file}")

            # Генерируем краткую сводку
            summary_content = generate_real_summary(services, staff_list)

            # Сохраняем сводку
            summary_file = "knowledge_base/services_real_summary.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)

            print(f"✅ Краткая сводка создана: {summary_file}")

            # Создаем JSON файл для бота
            json_content = generate_bot_json(services, staff_list)

            json_file = "knowledge_base/services_data.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_content)

            print(f"✅ JSON данные для бота созданы: {json_file}")

            print("\n🎉 База знаний успешно обновлена реальными данными!")
            return True

        else:
            print("⚠️ Получены мок данные, используем их как fallback")
            return False

    except Exception as e:
        print(f"❌ Ошибка при обновлении базы знаний: {str(e)}")
        return False


def generate_real_services_md(services, staff_list):
    """Генерирует markdown файл с реальными услугами"""

    content = f"""# LALIQ Beauty Studio - Реальные услуги из API

*Обновлено из YClients API: {datetime.now().strftime('%d.%m.%Y %H:%M')}*

## 📊 Общая информация
- **Всего услуг:** {len(services)}
- **Активных специалистов:** {len(staff_list)}
- **Ценовой диапазон:** {min(s.price for s in services):.0f} - {max(s.price for s in services):.0f} руб
- **Средняя стоимость:** {sum(s.price for s in services) / len(services):.0f} руб

"""

    # Группируем услуги по категориям на основе реальных данных
    categories = categorize_services(services)

    # Генерируем разделы
    for category, services_in_category in categories.items():
        if services_in_category:
            content += f"\n## {category}\n\n"

            # Сортируем услуги по цене
            services_in_category.sort(key=lambda x: x.price)

            for service in services_in_category:
                content += f"- **{service.title}** - {service.price:.0f} руб (ID: {service.id})\n"

    # Добавляем информацию о реальных специалистах
    content += f"\n## 👥 Наша команда специалистов\n\n"

    for staff in staff_list:
        content += f"### {staff.name}\n"
        content += f"**Специализация:** {staff.specialization}\n"
        content += f"**ID специалиста:** {staff.id}\n\n"

    content += f"""
## 📞 Контакты и запись

**LALIQ Beauty Studio Махачкала**
- 📍 Адрес: Махачкала, Россия
- 📞 Телефон: +7 988 264-73-44
- 🏢 Тип: Салон красоты

### Как записаться:
1. **Позвоните** по телефону +7 988 264-73-44
2. **Напишите** в наш Telegram-бот
3. **Укажите желаемую услугу** и удобное время
4. **Выберите специалиста** (или мы подберем оптимального)

---

*Данные получены из системы YClients. Актуальность: {datetime.now().strftime('%d.%m.%Y %H:%M')}*
"""

    return content


def categorize_services(services):
    """Категоризация услуг на основе реальных данных"""

    categories = {
        "💅 Маникюр и уход за руками": [],
        "🦶 Педикюр": [],
        "👁️ Брови и их оформление": [],
        "👁️ Ресницы и их наращивание": [],
        "🧴 Косметология лица": [],
        "💇‍♀️ Парикмахерские услуги": [],
        "🪒 Депиляция": [],
        "💉 Инъекционная косметология": [],
        "🎯 Специальные процедуры": []
    }

    for service in services:
        title_lower = service.title.lower()

        # Маникюр
        if any(word in title_lower for word in ['маникюр', 'гель-лак', 'наращивание ногтей', 'полировка ногтей', 'spa-уход для рук', 'забота о руках', 'снятие гель-лака']):
            categories["💅 Маникюр и уход за руками"].append(service)
        # Педикюр
        elif 'педикюр' in title_lower:
            categories["🦶 Педикюр"].append(service)
        # Брови
        elif any(word in title_lower for word in ['бров', 'коррекция бровей', 'окрашивание бровей', 'ламинирование бровей', 'ботокс для бровей', 'шелковые брови']):
            categories["👁️ Брови и их оформление"].append(service)
        # Ресницы
        elif any(word in title_lower for word in ['ресниц', 'наращивание ресниц', 'ламинирование ресниц', 'лучики', 'мокрый эффект', 'снятие наращенных ресниц']):
            categories["👁️ Ресницы и их наращивание"].append(service)
        # Косметология
        elif any(word in title_lower for word in ['чистка лица', 'пилинг', 'массаж лица', 'stop-акне', 'уход за кожей', 'glowface']):
            categories["🧴 Косметология лица"].append(service)
        # Парикмахерские услуги
        elif any(word in title_lower for word in ['стрижка', 'окрашивание', 'укладка', 'мытье головы', 'spa-уход для волос', 'кератиновое', 'наращивание волос', 'мелирование', 'тонирование', 'контуринг']):
            categories["💇‍♀️ Парикмахерские услуги"].append(service)
        # Депиляция
        elif any(word in title_lower for word in ['ноги', 'руки', 'бикини', 'подмышки', 'ягодицы', 'спина', 'живот', 'усики', 'подбородок', 'шея', 'баки', 'затылок', 'поясница', 'все тело']):
            categories["🪒 Депиляция"].append(service)
        # Инъекционная косметология
        elif any(word in title_lower for word in ['увеличение губ', 'коррекция', 'заполнение', 'мезотерапия']):
            categories["💉 Инъекционная косметология"].append(service)
        else:
            categories["🎯 Специальные процедуры"].append(service)

    return categories


def generate_real_summary(services, staff_list):
    """Генерирует краткую сводку реальных данных"""

    # Топ услуги по разным критериям
    cheapest = min(services, key=lambda x: x.price)
    most_expensive = max(services, key=lambda x: x.price)
    avg_price = sum(s.price for s in services) / len(services)

    # Популярные ценовые категории
    budget_services = [s for s in services if s.price < 1000]
    standard_services = [s for s in services if 1000 <= s.price < 3000]
    premium_services = [s for s in services if 3000 <= s.price < 8000]
    vip_services = [s for s in services if s.price >= 8000]

    content = f"""# Краткая сводка LALIQ Beauty Studio

*Реальные данные из API на {datetime.now().strftime('%d.%m.%Y %H:%M')}*

## 🏢 Основная информация
- **Салон:** LALIQ Beauty Studio Махачкала
- **Телефон:** +7 988 264-73-44
- **Всего услуг:** {len(services)}
- **Специалистов:** {len(staff_list)}

## 💰 Ценовая статистика
- **Самая доступная услуга:** {cheapest.title} - {cheapest.price:.0f} руб
- **Самая премиальная услуга:** {most_expensive.title} - {most_expensive.price:.0f} руб
- **Средняя стоимость услуги:** {avg_price:.0f} руб

## 📊 Ценовые категории
- **💚 Бюджетные** (до 1000 руб): {len(budget_services)} услуг
- **💙 Стандартные** (1000-3000 руб): {len(standard_services)} услуг
- **💜 Премиум** (3000-8000 руб): {len(premium_services)} услуг
- **💎 VIP** (от 8000 руб): {len(vip_services)} услуг

## 👥 Наши специалисты

"""

    for staff in staff_list:
        content += f"**{staff.name}** - {staff.specialization}\n"

    content += f"""

## 🔥 Топ-10 услуг по алфавиту

"""

    # Топ-10 услуг для быстрых ответов
    top_services = sorted(services, key=lambda x: x.title)[:10]
    for i, service in enumerate(top_services, 1):
        content += f"{i}. **{service.title}** - {service.price:.0f} руб\n"

    content += f"""

## 📞 Быстрая запись
Для записи на любую услугу звоните: **+7 988 264-73-44**

*Данные актуальны на {datetime.now().strftime('%d.%m.%Y %H:%M')}*
"""

    return content


def generate_bot_json(services, staff_list):
    """Генерирует JSON данные для бота"""

    import json

    data = {
        "salon_info": {
            "name": "LALIQ Beauty Studio Махачкала",
            "phone": "+7 988 264-73-44",
            "address": "Махачкала, Россия",
            "updated": datetime.now().isoformat()
        },
        "statistics": {
            "total_services": len(services),
            "total_staff": len(staff_list),
            "price_range": {
                "min": min(s.price for s in services),
                "max": max(s.price for s in services),
                "avg": sum(s.price for s in services) / len(services)
            }
        },
        "services": [
            {
                "id": service.id,
                "title": service.title,
                "price": service.price,
                "duration": service.duration
            }
            for service in services
        ],
        "staff": [
            {
                "id": staff.id,
                "name": staff.name,
                "specialization": staff.specialization
            }
            for staff in staff_list
        ]
    }

    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    """Основная функция"""
    try:
        print("🚀 Запуск финального обновления базы знаний...")
        success = asyncio.run(update_knowledge_base_final())

        if success:
            print("\n🎉 ФИНАЛЬНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("📁 Созданные файлы:")
            print("   - knowledge_base/salon_services_real.md")
            print("   - knowledge_base/services_real_summary.md")
            print("   - knowledge_base/services_data.json")
        else:
            print("\n⚠️ Не удалось получить реальные данные")

    except KeyboardInterrupt:
        print("\n⏹️ Обновление прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


