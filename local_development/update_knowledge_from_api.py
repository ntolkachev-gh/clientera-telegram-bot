#!/usr/bin/env python3
"""
Автоматическое обновление базы знаний из реального YClients API
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


async def update_knowledge_base():
    """Обновление базы знаний из реального API"""

    print("=" * 70)
    print("🔄 ОБНОВЛЕНИЕ БАЗЫ ЗНАНИЙ ИЗ YCLIENTS API")
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
        # Получаем реальные данные
        print("🔄 Получаем услуги из API...")
        services = await yclients.get_services(force_refresh=True, use_real_api=True)

        print("🔄 Получаем сотрудников из API...")
        staff_list = await yclients.get_staff(force_refresh=True, use_real_api=True)

        print(f"✅ Получено {len(services)} услуг и {len(staff_list)} сотрудников")

        # Генерируем обновленный файл услуг
        services_content = generate_services_md(services, staff_list)

        # Сохраняем файл
        services_file = "knowledge_base/salon_services_auto.md"
        with open(services_file, 'w', encoding='utf-8') as f:
            f.write(services_content)

        print(f"✅ Файл услуг обновлен: {services_file}")

        # Генерируем сводку для бота
        summary_content = generate_bot_summary(services, staff_list)

        # Сохраняем сводку
        summary_file = "knowledge_base/services_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)

        print(f"✅ Сводка для бота создана: {summary_file}")

        print("\n🎉 База знаний успешно обновлена!")

    except Exception as e:
        print(f"❌ Ошибка при обновлении базы знаний: {str(e)}")
        return False

    return True


def generate_services_md(services, staff_list):
    """Генерирует markdown файл с услугами"""

    content = f"""# Услуги LALIQ Beauty Studio Махачкала

*Автоматически обновлено из API: {datetime.now().strftime('%d.%m.%Y %H:%M')}*

## 📊 Общая информация
- **Всего услуг:** {len(services)}
- **Активных сотрудников:** {len(staff_list)}
- **Ценовой диапазон:** {min(s.price for s in services):.0f} - {max(s.price for s in services):.0f} руб

"""

    # Группируем услуги по категориям
    categories = {
        "💅 Маникюр и уход за руками": [],
        "🦶 Педикюр": [],
        "👁️ Брови": [],
        "👁️ Ресницы": [],
        "🧴 Косметология": [],
        "💇‍♀️ Парикмахерские услуги": [],
        "🪒 Депиляция": [],
        "💉 Инъекционная косметология": [],
        "🎯 Другие услуги": []
    }

    # Распределяем услуги по категориям
    for service in services:
        title_lower = service.title.lower()

        if any(word in title_lower for word in ['маникюр', 'наращивание ногтей', 'гель-лак', 'полировка', 'spa-уход для рук', 'забота о руках']):
            categories["💅 Маникюр и уход за руками"].append(service)
        elif 'педикюр' in title_lower:
            categories["🦶 Педикюр"].append(service)
        elif any(word in title_lower for word in ['бров', 'коррекция', 'окрашивание бровей']):
            categories["👁️ Брови"].append(service)
        elif any(word in title_lower for word in ['ресниц', 'ламинирование ресниц', 'лучики', 'мокрый эффект']):
            categories["👁️ Ресницы"].append(service)
        elif any(word in title_lower for word in ['чистка', 'пилинг', 'массаж лица', 'уход за кожей']):
            categories["🧴 Косметология"].append(service)
        elif any(word in title_lower for word in ['стрижка', 'окрашивание', 'укладка', 'мытье головы', 'spa-уход для волос', 'кератиновое', 'наращивание волос']):
            categories["💇‍♀️ Парикмахерские услуги"].append(service)
        elif any(word in title_lower for word in ['ноги', 'руки', 'бикини', 'подмышки', 'депиляция', 'усики', 'подбородок', 'спина', 'живот', 'все тело']):
            categories["🪒 Депиляция"].append(service)
        elif any(word in title_lower for word in ['увеличение', 'коррекция', 'заполнение', 'мезотерапия']):
            categories["💉 Инъекционная косметология"].append(service)
        else:
            categories["🎯 Другие услуги"].append(service)

    # Генерируем разделы
    for category, services_in_category in categories.items():
        if services_in_category:
            content += f"\n## {category}\n\n"

            # Сортируем услуги по цене
            services_in_category.sort(key=lambda x: x.price)

            for service in services_in_category:
                content += f"- **{service.title}** - {service.price:.0f} руб\n"

    # Добавляем информацию о специалистах
    content += f"\n## 👥 Наши специалисты\n\n"

    for staff in staff_list:
        content += f"### {staff.name}\n"
        content += f"**Специализация:** {staff.specialization}\n\n"

    content += f"""
## 📍 Контактная информация

**Название:** LALIQ Beauty Studio Махачкала
**Адрес:** Махачкала, Россия
**Телефон:** +7 988 264-73-44
**Тип заведения:** Салон красоты

---

*Данные автоматически получены из системы записи. Для записи и уточнения информации звоните по указанному телефону.*
"""

    return content


def generate_bot_summary(services, staff_list):
    """Генерирует краткую сводку для бота"""

    # Топ-10 популярных услуг (по алфавиту для примера)
    popular_services = sorted(services, key=lambda x: x.title)[:10]

    content = f"""# Краткая сводка услуг для бота

*Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}*

## Основная информация
- Салон: LALIQ Beauty Studio Махачкала
- Телефон: +7 988 264-73-44
- Всего услуг: {len(services)}
- Сотрудников: {len(staff_list)}

## Топ-10 услуг для быстрых ответов

"""

    for i, service in enumerate(popular_services, 1):
        content += f"{i}. **{service.title}** - {service.price:.0f} руб\n"

    content += f"""

## Специалисты

"""

    for staff in staff_list:
        content += f"- **{staff.name}** - {staff.specialization}\n"

    content += f"""

## Ценовые категории

- **Эконом** (до 1000 руб): {len([s for s in services if s.price < 1000])} услуг
- **Стандарт** (1000-3000 руб): {len([s for s in services if 1000 <= s.price < 3000])} услуг
- **Премиум** (3000-8000 руб): {len([s for s in services if 3000 <= s.price < 8000])} услуг
- **VIP** (от 8000 руб): {len([s for s in services if s.price >= 8000])} услуг

## Быстрые ответы

**Самая дешевая услуга:** {min(services, key=lambda x: x.price).title} - {min(s.price for s in services):.0f} руб
**Самая дорогая услуга:** {max(services, key=lambda x: x.price).title} - {max(s.price for s in services):.0f} руб
**Средняя стоимость:** {sum(s.price for s in services) / len(services):.0f} руб
"""

    return content


def main():
    """Основная функция"""
    try:
        print("🚀 Запуск обновления базы знаний...")
        success = asyncio.run(update_knowledge_base())

        if success:
            print("\n✅ Обновление завершено успешно!")
            print("📁 Проверьте файлы:")
            print("   - knowledge_base/salon_services_auto.md")
            print("   - knowledge_base/services_summary.md")
        else:
            print("\n❌ Обновление завершилось с ошибками")

    except KeyboardInterrupt:
        print("\n⏹️ Обновление прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
