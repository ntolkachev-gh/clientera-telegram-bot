#!/usr/bin/env python3
"""
Полная перестройка базы знаний из YClients API с правильным структурированием для чанков Qdrant
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.yclients_client import YclientsClient
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeBaseBuilder:
    """Построитель базы знаний из API данных"""

    def __init__(self):
        self.kb_dir = Path("knowledge_base")
        self.kb_dir.mkdir(exist_ok=True)

        # Инициализируем YClients клиент с реальными данными
        # Используем проверенные данные из отчетов интеграции
        real_company_id = "1297379"
        real_api_key = "nmnsgmfcpdu65db2b5kp"

        self.yclients = YclientsClient(
            api_key=real_api_key,
            company_id=real_company_id
        )

        # Данные из API
        self.services = []
        self.staff = []
        self.company_info = {}

    async def clear_knowledge_base(self):
        """Очистка старой базы знаний"""
        print("🗑️  ОЧИСТКА БАЗЫ ЗНАНИЙ")
        print("=" * 50)

        # Удаляем все MD файлы в knowledge_base
        for md_file in self.kb_dir.glob("*.md"):
            md_file.unlink()
            print(f"❌ Удален: {md_file.name}")

        print(f"✅ Директория {self.kb_dir} очищена")
        print()

    async def fetch_api_data(self):
        """Загрузка всех данных из API"""
        print("📡 ЗАГРУЗКА ДАННЫХ ИЗ API")
        print("=" * 50)

        try:
            # Получаем услуги
            print("🔄 Загружаем услуги...")
            self.services = await self.yclients.get_services(
                force_refresh=True,
                use_real_api=True
            )
            print(f"✅ Загружено {len(self.services)} услуг")

            # Получаем сотрудников
            print("🔄 Загружаем сотрудников...")
            self.staff = await self.yclients.get_staff(
                force_refresh=True,
                use_real_api=True
            )
            print(f"✅ Загружено {len(self.staff)} сотрудников")

            # Добавляем базовую информацию о компании
            self.company_info = {
                "name": "LALIQ Beauty Studio",
                "location": "Махачкала",
                "phone": "+7 988 264-73-44",
                "type": "Салон красоты",
                "total_services": len(self.services),
                "total_staff": len(self.staff),
                "last_updated": datetime.now().isoformat()
            }

            print("✅ Все данные загружены успешно")
            print()

        except Exception as e:
            print(f"❌ Ошибка при загрузке данных: {str(e)}")
            raise

    def categorize_services(self) -> Dict[str, List]:
        """Категоризация услуг для структурирования"""
        categories = {
            "manicure": {
                "name": "Маникюр и уход за руками",
                "icon": "💅",
                "services": [],
                "keywords": ['маникюр', 'наращивание ногтей', 'гель-лак', 'полировка', 'spa-уход для рук', 'забота о руках', 'покрытие', 'френч']
            },
            "pedicure": {
                "name": "Педикюр",
                "icon": "🦶",
                "services": [],
                "keywords": ['педикюр']
            },
            "eyebrows": {
                "name": "Брови",
                "icon": "👁️",
                "services": [],
                "keywords": ['бров', 'коррекция бровей', 'окрашивание бровей', 'моделирование']
            },
            "eyelashes": {
                "name": "Ресницы",
                "icon": "👁️",
                "services": [],
                "keywords": ['ресниц', 'ламинирование ресниц', 'лучики', 'мокрый эффект', 'наращивание ресниц']
            },
            "cosmetology": {
                "name": "Косметология",
                "icon": "🧴",
                "services": [],
                "keywords": ['чистка', 'пилинг', 'массаж лица', 'уход за кожей', 'лечение акне']
            },
            "hair": {
                "name": "Парикмахерские услуги",
                "icon": "💇‍♀️",
                "services": [],
                "keywords": ['стрижка', 'окрашивание', 'укладка', 'мытье головы', 'spa-уход для волос', 'кератиновое', 'наращивание волос', 'химическая завивка']
            },
            "depilation": {
                "name": "Депиляция",
                "icon": "🪒",
                "services": [],
                "keywords": ['депиляция', 'эпиляция', 'воск', 'шугаринг', 'ноги', 'руки', 'бикини', 'подмышки', 'усики', 'подбородок', 'спина', 'живот', 'все тело']
            },
            "injections": {
                "name": "Инъекционная косметология",
                "icon": "💉",
                "services": [],
                "keywords": ['увеличение', 'коррекция губ', 'заполнение', 'мезотерапия', 'ботокс', 'филлер']
            },
            "other": {
                "name": "Другие услуги",
                "icon": "🎯",
                "services": [],
                "keywords": []
            }
        }

        # Распределяем услуги по категориям
        for service in self.services:
            title_lower = service.title.lower()
            categorized = False

            for cat_key, cat_data in categories.items():
                if cat_key == 'other':
                    continue

                if any(keyword in title_lower for keyword in cat_data['keywords']):
                    cat_data['services'].append(service)
                    categorized = True
                    break

            # Если не попала ни в одну категорию - в "Другие"
            if not categorized:
                categories['other']['services'].append(service)

        return categories

    def generate_salon_info_md(self) -> str:
        """Генерация основной информации о салоне"""
        content = f"""# LALIQ Beauty Studio - Информация о салоне

## Основная информация
- **Название:** {self.company_info['name']}
- **Расположение:** {self.company_info['location']}
- **Телефон:** {self.company_info['phone']}
- **Тип заведения:** {self.company_info['type']}

## Статистика
- **Всего услуг:** {self.company_info['total_services']}
- **Специалистов:** {self.company_info['total_staff']}
- **Последнее обновление:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

## Контакты и запись
Для записи на услуги звоните по телефону: **{self.company_info['phone']}**

Наши специалисты помогут подобрать подходящие услуги и найти удобное время для визита.

## Режим работы
Уточняйте актуальное расписание работы по телефону.

---
*Данные автоматически получены из системы управления салоном*
"""
        return content

    def generate_services_by_category_md(self, categories: Dict[str, Dict]) -> Dict[str, str]:
        """Генерация MD файлов по категориям услуг"""
        md_files = {}

        for cat_key, cat_data in categories.items():
            if not cat_data['services']:
                continue

            # Сортируем услуги по цене
            services = sorted(cat_data['services'], key=lambda x: x.price)

            content = f"""# {cat_data['icon']} {cat_data['name']} - LALIQ Beauty Studio

## Доступные услуги

"""

            for service in services:
                content += f"""### {service.title}
- **Цена:** {service.price:.0f} руб
- **Длительность:** {service.duration} мин
- **ID услуги:** {service.id}

"""

            # Добавляем информацию о специалистах для этой категории
            relevant_staff = []
            service_ids = [s.id for s in services]

            for staff_member in self.staff:
                if staff_member.service_ids:
                    # Проверяем пересечение услуг
                    if any(sid in service_ids for sid in staff_member.service_ids):
                        relevant_staff.append(staff_member)

            if relevant_staff:
                content += f"""## Наши специалисты

"""
                for staff_member in relevant_staff:
                    content += f"""### {staff_member.name}
**Специализация:** {staff_member.specialization}

"""

            content += f"""## Запись на услуги

Для записи на любую услугу из категории "{cat_data['name']}" звоните по телефону: **+7 988 264-73-44**

---
*Цены и услуги актуальны на {datetime.now().strftime('%d.%m.%Y')}*
"""

            filename = f"{cat_key}_services.md"
            md_files[filename] = content

        return md_files

    def generate_staff_md(self) -> str:
        """Генерация информации о специалистах"""
        content = f"""# 👥 Специалисты LALIQ Beauty Studio

## Наша команда

"""

        for staff_member in self.staff:
            content += f"""### {staff_member.name}
**Специализация:** {staff_member.specialization}
**ID специалиста:** {staff_member.id}

"""

            # Добавляем услуги, которые может выполнять специалист
            if staff_member.service_ids:
                staff_services = [s for s in self.services if s.id in staff_member.service_ids]
                if staff_services:
                    content += "**Выполняемые услуги:**\n"
                    for service in staff_services:
                        content += f"- {service.title} ({service.price:.0f} руб)\n"
                    content += "\n"

        content += f"""## Запись к специалисту

Для записи к конкретному специалисту звоните по телефону: **+7 988 264-73-44**

Наши администраторы помогут выбрать подходящего мастера и удобное время.

---
*Информация о специалистах обновлена {datetime.now().strftime('%d.%m.%Y %H:%M')}*
"""

        return content

    def generate_pricing_md(self) -> str:
        """Генерация информации о ценах"""
        if not self.services:
            return "# Прайс-лист пуст"

        # Сортируем услуги по цене
        services_by_price = sorted(self.services, key=lambda x: x.price)

        min_price = min(s.price for s in self.services)
        max_price = max(s.price for s in self.services)
        avg_price = sum(s.price for s in self.services) / len(self.services)

        content = f"""# 💰 Прайс-лист LALIQ Beauty Studio

## Ценовая информация

- **Минимальная цена:** {min_price:.0f} руб
- **Максимальная цена:** {max_price:.0f} руб
- **Средняя стоимость услуг:** {avg_price:.0f} руб
- **Всего услуг в прайсе:** {len(self.services)}

## Все услуги по цене

"""

        # Группируем по ценовым категориям
        price_categories = {
            "Эконом (до 1000 руб)": [s for s in services_by_price if s.price < 1000],
            "Стандарт (1000-3000 руб)": [s for s in services_by_price if 1000 <= s.price < 3000],
            "Премиум (3000-8000 руб)": [s for s in services_by_price if 3000 <= s.price < 8000],
            "VIP (от 8000 руб)": [s for s in services_by_price if s.price >= 8000]
        }

        for category, services in price_categories.items():
            if services:
                content += f"""### {category}

"""
                for service in services:
                    content += f"- **{service.title}** — {service.price:.0f} руб ({service.duration} мин)\n"
                content += "\n"

        content += f"""## Полный список по алфавиту

"""

        # Сортируем по алфавиту
        services_alphabetical = sorted(self.services, key=lambda x: x.title)

        for service in services_alphabetical:
            content += f"- **{service.title}** — {service.price:.0f} руб ({service.duration} мин)\n"

        content += f"""

---
*Прайс-лист актуален на {datetime.now().strftime('%d.%m.%Y %H:%M')}*
*Для записи звоните: +7 988 264-73-44*
"""

        return content

    def generate_booking_info_md(self) -> str:
        """Генерация информации о записи"""
        content = f"""# 📅 Запись в LALIQ Beauty Studio

## Как записаться

### Телефон для записи
**+7 988 264-73-44**

Наши администраторы работают и помогут:
- Подобрать подходящие услуги
- Выбрать удобное время
- Записать к нужному специалисту
- Ответить на все вопросы

## Доступные услуги

У нас доступно **{len(self.services)} различных услуг** в следующих категориях:

"""

        # Добавляем краткий обзор категорий
        categories = self.categorize_services()

        for cat_data in categories.values():
            if cat_data['services']:
                content += f"- **{cat_data['icon']} {cat_data['name']}** — {len(cat_data['services'])} услуг\n"

        content += f"""

## Наши специалисты

В салоне работает **{len(self.staff)} специалистов**:

"""

        for staff_member in self.staff:
            content += f"- **{staff_member.name}** — {staff_member.specialization}\n"

        content += f"""

## Рекомендации по записи

1. **Заранее планируйте визит** — популярные мастера могут быть заняты
2. **Уточняйте время процедур** — некоторые услуги занимают несколько часов
3. **Сообщайте о предпочтениях** — мы поможем выбрать подходящего специалиста
4. **Приходите вовремя** — это поможет избежать задержек

## Отмена и перенос записи

Если планы изменились, обязательно позвоните нам заранее для переноса или отмены записи.

---
*Информация актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}*
"""

        return content

    async def save_all_md_files(self):
        """Сохранение всех MD файлов"""
        print("💾 СОЗДАНИЕ MD ФАЙЛОВ")
        print("=" * 50)

        # 1. Основная информация о салоне
        salon_info = self.generate_salon_info_md()
        salon_file = self.kb_dir / "salon_info.md"
        with open(salon_file, 'w', encoding='utf-8') as f:
            f.write(salon_info)
        print(f"✅ Создан: {salon_file.name}")

        # 2. Услуги по категориям
        categories = self.categorize_services()
        category_files = self.generate_services_by_category_md(categories)

        for filename, content in category_files.items():
            file_path = self.kb_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Создан: {filename}")

        # 3. Информация о специалистах
        staff_info = self.generate_staff_md()
        staff_file = self.kb_dir / "staff_info.md"
        with open(staff_file, 'w', encoding='utf-8') as f:
            f.write(staff_info)
        print(f"✅ Создан: {staff_file.name}")

        # 4. Прайс-лист
        pricing_info = self.generate_pricing_md()
        pricing_file = self.kb_dir / "pricing.md"
        with open(pricing_file, 'w', encoding='utf-8') as f:
            f.write(pricing_info)
        print(f"✅ Создан: {pricing_file.name}")

        # 5. Информация о записи
        booking_info = self.generate_booking_info_md()
        booking_file = self.kb_dir / "booking_info.md"
        with open(booking_file, 'w', encoding='utf-8') as f:
            f.write(booking_info)
        print(f"✅ Создан: {booking_file.name}")

        print(f"\n✅ Создано {len(category_files) + 4} MD файлов")
        print()

    def generate_chunks_mapping(self) -> Dict[str, Any]:
        """Генерация маппинга для чанков Qdrant"""
        chunks_info = {
            "created_at": datetime.now().isoformat(),
            "total_files": 0,
            "files": {},
            "categories": {},
            "chunk_strategy": {
                "description": "Каждый MD файл = отдельный чанк в Qdrant",
                "reasoning": "Разделение по смысловым группам для лучшего поиска"
            }
        }

        # Информация о файлах
        md_files = list(self.kb_dir.glob("*.md"))
        chunks_info["total_files"] = len(md_files)

        for md_file in md_files:
            file_size = md_file.stat().st_size
            chunks_info["files"][md_file.name] = {
                "size_bytes": file_size,
                "chunk_type": self._get_chunk_type(md_file.name),
                "priority": self._get_chunk_priority(md_file.name)
            }

        # Информация о категориях услуг
        categories = self.categorize_services()
        for cat_key, cat_data in categories.items():
            if cat_data['services']:
                chunks_info["categories"][cat_key] = {
                    "name": cat_data['name'],
                    "icon": cat_data['icon'],
                    "services_count": len(cat_data['services']),
                    "filename": f"{cat_key}_services.md"
                }

        return chunks_info

    def _get_chunk_type(self, filename: str) -> str:
        """Определение типа чанка по имени файла"""
        if filename == "salon_info.md":
            return "general_info"
        elif filename == "staff_info.md":
            return "staff"
        elif filename == "pricing.md":
            return "pricing"
        elif filename == "booking_info.md":
            return "booking"
        elif filename.endswith("_services.md"):
            return "services_category"
        else:
            return "other"

    def _get_chunk_priority(self, filename: str) -> int:
        """Определение приоритета чанка (1 = высший)"""
        priority_map = {
            "salon_info.md": 1,
            "booking_info.md": 1,
            "pricing.md": 2,
            "staff_info.md": 3
        }

        if filename in priority_map:
            return priority_map[filename]
        elif filename.endswith("_services.md"):
            return 2  # Услуги имеют высокий приоритет
        else:
            return 5

    async def create_chunks_info_file(self):
        """Создание файла с информацией о чанках"""
        print("📊 СОЗДАНИЕ ИНФОРМАЦИИ О ЧАНКАХ")
        print("=" * 50)

        chunks_info = self.generate_chunks_mapping()

        # Сохраняем как JSON для программного использования
        chunks_json_file = self.kb_dir / "chunks_mapping.json"
        with open(chunks_json_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_info, f, ensure_ascii=False, indent=2)
        print(f"✅ Создан: {chunks_json_file.name}")

        # Создаем человекочитаемую версию
        chunks_md_content = f"""# 📊 Структура чанков для Qdrant

## Общая информация
- **Создано:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
- **Всего файлов:** {chunks_info['total_files']}
- **Стратегия чанков:** {chunks_info['chunk_strategy']['description']}

## Файлы и их типы

"""

        # Группируем по типам
        files_by_type = {}
        for filename, file_info in chunks_info['files'].items():
            chunk_type = file_info['chunk_type']
            if chunk_type not in files_by_type:
                files_by_type[chunk_type] = []
            files_by_type[chunk_type].append((filename, file_info))

        for chunk_type, files in files_by_type.items():
            chunks_md_content += f"### {chunk_type}\n"
            for filename, file_info in sorted(files, key=lambda x: x[1]['priority']):
                size_kb = file_info['size_bytes'] / 1024
                chunks_md_content += f"- **{filename}** (приоритет: {file_info['priority']}, размер: {size_kb:.1f} KB)\n"
            chunks_md_content += "\n"

        chunks_md_content += """## Рекомендации по использованию в Qdrant

1. **Высокий приоритет** (priority 1-2) — чанки для основных запросов
2. **Средний приоритет** (priority 3-4) — специализированная информация
3. **Низкий приоритет** (priority 5+) — дополнительные данные

## Обновление чанков

При обновлении базы знаний:
1. Удалить все существующие чанки
2. Загрузить новые файлы как отдельные чанки
3. Настроить метаданные согласно chunks_mapping.json

---
*Автоматически создано системой управления базой знаний*
"""

        chunks_md_file = self.kb_dir / "chunks_info.md"
        with open(chunks_md_file, 'w', encoding='utf-8') as f:
            f.write(chunks_md_content)
        print(f"✅ Создан: {chunks_md_file.name}")
        print()

    async def rebuild_complete_knowledge_base(self):
        """Полная перестройка базы знаний"""
        print("🚀 ПОЛНАЯ ПЕРЕСТРОЙКА БАЗЫ ЗНАНИЙ")
        print("=" * 70)
        print()

        try:
            # 1. Очистка
            await self.clear_knowledge_base()

            # 2. Загрузка данных из API
            await self.fetch_api_data()

            # 3. Создание MD файлов
            await self.save_all_md_files()

            # 4. Создание информации о чанках
            await self.create_chunks_info_file()

            print("🎉 БАЗА ЗНАНИЙ УСПЕШНО ПЕРЕСТРОЕНА!")
            print("=" * 70)
            print(f"📁 Директория: {self.kb_dir.absolute()}")
            print(f"📄 Создано файлов: {len(list(self.kb_dir.glob('*.md')))}")
            print(f"📊 Услуг загружено: {len(self.services)}")
            print(f"👥 Специалистов: {len(self.staff)}")
            print()
            print("📋 Созданные файлы:")
            for md_file in sorted(self.kb_dir.glob("*.md")):
                size_kb = md_file.stat().st_size / 1024
                print(f"  - {md_file.name} ({size_kb:.1f} KB)")
            print()

            return True

        except Exception as e:
            print(f"❌ ОШИБКА ПРИ ПЕРЕСТРОЙКЕ: {str(e)}")
            logger.exception("Детали ошибки:")
            return False


async def main():
    """Основная функция"""
    try:
        builder = KnowledgeBaseBuilder()
        success = await builder.rebuild_complete_knowledge_base()

        if success:
            print("✅ Перестройка завершена успешно!")
            print("\n📝 Следующие шаги:")
            print("1. Проверьте созданные MD файлы в knowledge_base/")
            print("2. Используйте chunks_mapping.json для загрузки в Qdrant")
            print("3. Обновите векторную базу данных")
        else:
            print("❌ Перестройка завершилась с ошибками")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        logger.exception("Детали:")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
