"""
Определение OpenAI Function Calling tools для работы с Yclients API и Qdrant
"""
import logging
import json
import re
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bot.embedding import EmbeddingService
from database.models import Appointment, Client
from database.database import SessionLocal

logger = logging.getLogger(__name__)


class YclientsToolsDefinition:
    """Класс для определения tools (функций) OpenAI Function Calling"""

    @staticmethod
    def get_tools_schema() -> List[Dict[str, Any]]:
        """
        Получить схемы всех доступных tools для OpenAI Function Calling

        Returns:
            Список схем функций в формате OpenAI
        """
        logger.info("YTD_GTS: Формирование схем tools для OpenAI Function Calling")
        logger.info("YTD_GTS: Создаем схемы для следующих tools:")
        logger.info("YTD_GTS:   get_services - получение списка услуг из Youclients API")
        logger.info("YTD_GTS:   get_staff - получение списка мастеров")
        logger.info("YTD_GTS:   find_service_by_name - поиск услуги по названию")
        logger.info("YTD_GTS:   find_staff_by_name - поиск мастера по имени")
        logger.info("YTD_GTS:   get_available_slots - получение свободных слотов")
        logger.info("YTD_GTS:   get_available_days - получение доступных дней")
        logger.info("YTD_GTS:   get_available_times - получение временных слотов")
        logger.info("YTH_GTS:   create_booking - создание записи")

        tools = [
            YclientsToolsDefinition._get_services_tool(),
            YclientsToolsDefinition._get_staff_tool(),
            YclientsToolsDefinition._find_service_by_name_tool(),
            YclientsToolsDefinition._find_staff_by_name_tool(),
            YclientsToolsDefinition._get_available_slots_tool(),
            YclientsToolsDefinition._get_available_days_tool(),
            YclientsToolsDefinition._get_available_times_tool(),
            YclientsToolsDefinition._create_booking_tool()
        ]

        logger.info(f"YTD_GTS: Успешно создано {len(tools)} схем tools для OpenAI")
        logger.info("YTD_GTS: Tools готовы к использованию в OpenAI Function Calling")
        logger.info(f"YTD_GTS: Полный список созданных tools: {[tool['function']['name'] for tool in tools]}")
        return tools

    @staticmethod
    def _get_services_tool() -> Dict[str, Any]:
        """Схема tool для получения списка услуг"""
        return {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": "Получить актуальный список доступных услуг салона красоты с ценами и длительностью из Youclients API",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    @staticmethod
    def _get_staff_tool() -> Dict[str, Any]:
        """Схема tool для получения списка мастеров"""
        return {
            "type": "function",
            "function": {
                "name": "get_staff",
                "description": "Получить список мастеров салона с их специализацией",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    @staticmethod
    def _find_service_by_name_tool() -> Dict[str, Any]:
        """Схема tool для поиска услуги по названию"""
        return {
            "type": "function",
            "function": {
                "name": "find_service_by_name",
                "description": "Найти услугу по названию (поддерживает нечеткий поиск)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Название услуги для поиска"
                        }
                    },
                    "required": ["service_name"]
                }
            }
        }

    @staticmethod
    def _find_staff_by_name_tool() -> Dict[str, Any]:
        """Схема tool для поиска мастера по имени"""
        return {
            "type": "function",
            "function": {
                "name": "find_staff_by_name",
                "description": "Найти мастера по имени",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "staff_name": {
                            "type": "string",
                            "description": "Имя мастера для поиска"
                        }
                    },
                    "required": ["staff_name"]
                }
            }
        }

    @staticmethod
    def _get_available_slots_tool() -> Dict[str, Any]:
        """Схема tool для поиска свободных временных слотов"""
        return {
            "type": "function",
            "function": {
                "name": "get_available_slots",
                "description": "Найти свободные временные слоты для записи",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Список ID услуг"
                        },
                        "date_from": {
                            "type": "string",
                            "format": "date",
                            "description": "Начальная дата поиска в формате YYYY-MM-DD"
                        },
                        "date_to": {
                            "type": "string",
                            "format": "date",
                            "description": "Конечная дата поиска в формате YYYY-MM-DD"
                        },
                        "staff_id": {
                            "type": "integer",
                            "description": "ID конкретного мастера (опционально)"
                        }
                    },
                    "required": ["service_ids", "date_from", "date_to"]
                }
            }
        }

    @staticmethod
    def _create_booking_tool() -> Dict[str, Any]:
        """Схема tool для создания записи"""
        return {
            "type": "function",
            "function": {
                "name": "create_booking",
                "description": "Создать запись клиента на услугу",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "Телефон клиента"
                        },
                        "fullname": {
                            "type": "string",
                            "description": "Полное имя клиента"
                        },
                        "email": {
                            "type": "string",
                            "description": "Email клиента (опционально)"
                        },
                        "service_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Список ID услуг"
                        },
                        "staff_id": {
                            "type": "integer",
                            "description": "ID мастера"
                        },
                        "booking_datetime": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Дата и время записи в формате ISO"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Комментарий к записи (опционально)"
                        }
                    },
                    "required": ["phone", "fullname", "service_ids", "staff_id", "booking_datetime"]
                }
            }
        }

    @staticmethod
    def _get_available_days_tool() -> Dict[str, Any]:
        """Схема tool для получения доступных дней для записи к сотруднику"""
        return {
            "type": "function",
            "function": {
                "name": "get_available_days",
                "description": "Получить доступные дни для записи к указанному сотруднику и услуге",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "staff_id": {
                            "type": "integer",
                            "description": "ID сотрудника"
                        },
                        "service_id": {
                            "type": "integer",
                            "description": "ID услуги"
                        }
                    },
                    "required": ["staff_id", "service_id"]
                }
            }
        }

    @staticmethod
    def _get_available_times_tool() -> Dict[str, Any]:
        """Схема tool для получения доступных временных слотов на конкретную дату"""
        return {
            "type": "function",
            "function": {
                "name": "get_available_times",
                "description": "Получить доступные временные слоты на конкретную дату для указанного сотрудника и услуги",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "staff_id": {
                            "type": "integer",
                            "description": "ID сотрудника"
                        },
                        "service_id": {
                            "type": "integer",
                            "description": "ID услуги"
                        },
                        "day": {
                            "type": "string",
                            "description": "Дата в формате YYYY-MM-DD или timestamp"
                        }
                    },
                    "required": ["staff_id", "service_id", "day"]
                }
            }
        }


class YclientsToolsHandler:
    """Класс для обработки вызовов tools"""

    def __init__(self, yclients_client, telegram_id: str = None):
        """
        Инициализация обработчика tools

        Args:
            yclients_client: экземпляр YclientsClient для выполнения операций
            telegram_id: ID пользователя Telegram для записи в БД
        """
        self.yclients = yclients_client
        self.telegram_id = telegram_id
        self.embedding_service = EmbeddingService()
        logger.info("YTH_INIT: Инициализирован YclientsToolsHandler")
        logger.info(f"YTH_INIT: YclientsClient: {type(yclients_client).__name__}")
        logger.info(f"YTH_INIT: Telegram ID: {telegram_id}")
        logger.info("YTH_INIT: Готов к обработке вызовов tools")

    def get_tool_functions(self) -> Dict[str, callable]:
        """
        Получить мапинг функций для вызова tools

        Returns:
            Словарь с именами функций и их обработчиками
        """
        logger.info("YTH_GTF: Получение маппинга функций для tools")
        tool_functions = {
            "get_services": self.handle_get_services,
            "get_staff": self.handle_get_staff,
            "find_service_by_name": self.handle_find_service_by_name,
            "find_staff_by_name": self.handle_find_staff_by_name,
            "get_available_slots": self.handle_get_available_slots,
            "get_available_days": self.handle_get_available_days,
            "get_available_times": self.handle_get_available_times,
            "create_booking": self.handle_create_booking
        }
        logger.info(f"YTH_GTF: Зарегистрировано {len(tool_functions)} функций для tools")
        logger.info(f"YTH_GTF: Доступные функции: {list(tool_functions.keys())}")
        return tool_functions

    # ============================================================================
    # ОБРАБОТЧИКИ TOOLS
    # ============================================================================

    async def handle_get_services(self, **kwargs) -> Dict[str, Any]:
        """Tool handler: получить полный список услуг из Youclients Proxy API"""
        logger.info("YTH_HGS: Обработка tool: get_services")
        logger.info(f"YTH_HGS: Параметры вызова: {kwargs}")
        logger.info(f"YTH_HGS: Полные параметры kwargs: {json.dumps(kwargs, ensure_ascii=False, indent=2) if kwargs else 'None'}")

        try:
            logger.info("YTH_HGS: Получение всех услуг из Youclients Proxy API...")

            # Получаем услуги из API
            services = await self._get_services_from_api()

            logger.info(f"YTH_HGS: Найдено {len(services)} услуг в API")
            logger.info(f"YTH_HGS: Успешно обработано {len(services)} услуг")

            if services:
                logger.info(f"YTH_HGS: Первые 3 услуги: {services[:3]}")
                logger.info(f"YTH_HGS: Полный список названий услуг: {[s.get('title', 'Unknown') for s in services]}")

            return {
                "services": services,
                "total_count": len(services),
                "success": True
            }

        except Exception as e:
            logger.error(f"YTH_HGS: Ошибка в tool get_services: {e}")
            logger.error(f"YTH_HGS: Тип ошибки: {type(e).__name__}")
            logger.error(f"YTH_HGS: Полная информация об ошибке: {str(e)}", exc_info=True)
            return {"error": str(e), "success": False}

    async def _get_services_from_api(self) -> List[Dict[str, Any]]:
        """Получить все услуги из Youclients Proxy API"""
        try:
            logger.info("YTH_GSA: Начало получения услуг из Youclients Proxy API")

            # URL для получения услуг
            api_url = "https://clientera-yclients-proxy-7fb108aebb90.herokuapp.com/api/v1/services"

            logger.info(f"YTH_GSA: Отправляем запрос к API: {api_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"YTH_GSA: Получен ответ от API, статус: {response.status}")

                        if data.get("success") and "services" in data:
                            services = data["services"]
                            logger.info(f"YTH_GSA: Успешно получено {len(services)} услуг из API")

                            # Преобразуем данные в нужный формат
                            formatted_services = []
                            for service in services:
                                formatted_service = {
                                    "id": service.get("id"),
                                    "title": service.get("title"),
                                    "price": service.get("price"),
                                    "price_display": service.get("price_display"),
                                    "duration": service.get("duration"),
                                    "category": service.get("category"),
                                    "specialist": service.get("specialist"),
                                    "description": service.get("description")
                                }
                                formatted_services.append(formatted_service)

                            return formatted_services
                        else:
                            logger.error(f"YTH_GSA: API вернул неуспешный ответ: {data}")
                            raise Exception(f"API вернул неуспешный ответ: {data}")
                    else:
                        logger.error(f"YTH_GSA: HTTP ошибка: {response.status}")
                        raise Exception(f"HTTP ошибка при получении услуг: {response.status}")

        except Exception as e:
            logger.error(f"YTH_GSA: Ошибка при получении услуг из API: {e}")
            logger.error(f"YTH_GTS: Полная информация об ошибке: {str(e)}", exc_info=True)
            raise

    def _parse_services_from_content(self, content: str, category: str,
                                   specialist: Optional[str] = None,
                                   has_prices: bool = False,
                                   price_range: Dict = None) -> List[Dict[str, Any]]:
        """Парсинг услуг из контента с улучшенными регулярными выражениями для реального формата данных"""
        services = []
        lines = content.split('\n')

        current_service_name = None
        current_price = None
        current_duration = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Ищем заголовки услуг (### Название услуги)
            if line.startswith('### ') and not line.startswith('#### '):
                current_service_name = line.replace('### ', '').strip()
                current_price = None
                current_duration = None

                # Ищем цену и длительность в следующих строках
                j = i + 1
                while j < len(lines) and j < i + 5:  # Ищем в следующих 5 строках
                    next_line = lines[j].strip()

                    # Ищем цену: - **Цена:** 590 руб
                    price_match = re.search(r'-\s*\*\*Цена:\*\*\s*(\d+)\s*(?:₽|руб)', next_line, re.IGNORECASE)
                    if price_match:
                        current_price = int(price_match.group(1))

                    # Ищем длительность: - **Длительность:** 60 мин
                    duration_match = re.search(r'-\s*\*\*Длительность:\*\*\s*(\d+)\s*мин', next_line, re.IGNORECASE)
                    if duration_match:
                        current_duration = int(duration_match.group(1))

                    # Если дошли до следующего заголовка, прерываем поиск
                    if next_line.startswith('###') or next_line.startswith('##'):
                        break

                    j += 1

                # Если нашли и название, и цену, добавляем услугу
                if current_service_name and current_price:
                    # Используем найденную длительность или оценочную
                    duration = current_duration if current_duration else self._estimate_service_duration(current_service_name, category)

                    services.append({
                        "id": len(services) + 1,
                        "title": current_service_name,
                        "price": current_price,
                        "price_display": f"{current_price} ₽",
                        "duration": duration,
                        "category": self._normalize_category_name(category),
                        "specialist": specialist,
                        "description": ""
                    })

            i += 1

        # Fallback: если не нашли услуги в новом формате, пробуем старые паттерны
        if not services:
            for line in lines:
                line = line.strip()

                # Пропускаем заголовки и пустые строки
                if not line or line.startswith('#') or line.startswith('**'):
                    continue

                # Паттерны для поиска услуг с ценами (старый формат)
                patterns = [
                    # Формат: "- Название услуги — 1500 ₽"
                    r'^-\s*(.+?)\s*[—–-]\s*(\d+(?:\s*-\s*\d+)?)\s*₽',
                    # Формат: "• Название услуги - 1500 руб"
                    r'^[•-]\s*(.+?)\s*[-—–]\s*(\d+(?:\s*-\s*\d+)?)\s*(?:₽|руб)',
                    # Формат: "Название услуги: 1500 ₽"
                    r'^(.+?):\s*(\d+(?:\s*-\s*\d+)?)\s*₽',
                    # Формат: "1. Название услуги - 1500 ₽"
                    r'^\d+\.\s*(.+?)\s*[-—–]\s*(\d+(?:\s*-\s*\d+)?)\s*₽'
                ]

                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        service_name = match.group(1).strip()
                        price_str = match.group(2).strip()

                        # Очищаем название от лишних символов
                        service_name = re.sub(r'^[•\-\*\d\.\s]+', '', service_name).strip()
                        service_name = service_name.replace('**', '').strip()

                        # Парсим цену (может быть диапазон)
                        if '-' in price_str and not price_str.startswith('-'):
                            # Диапазон цен: "1500-2000"
                            price_parts = price_str.split('-')
                            try:
                                min_price = int(price_parts[0].strip())
                                max_price = int(price_parts[1].strip())
                                price = min_price  # Берем минимальную цену
                                price_display = f"{min_price}-{max_price} ₽"
                            except ValueError:
                                price = int(re.search(r'\d+', price_str).group())
                                price_display = f"{price} ₽"
                        else:
                            try:
                                price = int(re.search(r'\d+', price_str).group())
                                price_display = f"{price} ₽"
                            except (ValueError, AttributeError):
                                continue

                        # Определяем длительность на основе типа услуги
                        duration = self._estimate_service_duration(service_name, category)

                        services.append({
                            "id": len(services) + 1,
                            "title": service_name,
                            "price": price,
                            "price_display": price_display,
                            "duration": duration,
                            "category": self._normalize_category_name(category),
                            "specialist": specialist,
                            "description": ""  # Можно расширить парсингом описания
                        })
                        break

        return services

    def _estimate_service_duration(self, service_name: str, category: str) -> int:
        """Оценка длительности услуги на основе названия и категории"""
        service_lower = service_name.lower()
        category_lower = category.lower()

        # Длительные процедуры
        if any(word in service_lower for word in ['наращивание', 'ламинирование', 'биозавивка', 'окрашивание']):
            return 120

        # Процедуры средней длительности
        if any(word in service_lower for word in ['маникюр', 'педикюр', 'массаж', 'чистка', 'пилинг']):
            return 60

        # Инъекционные процедуры
        if 'инъекц' in category_lower or any(word in service_lower for word in ['ботокс', 'филлер', 'мезотерапия']):
            return 45

        # Быстрые процедуры
        if any(word in service_lower for word in ['покрытие', 'коррекция', 'снятие', 'консультация']):
            return 30

        # По умолчанию
        return 60

    def _parse_service_from_content(self, content: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Парсинг конкретной услуги из контента"""
        lines = content.split('\n')

        # Ищем строки, содержащие название услуги
        for i, line in enumerate(lines):
            line_lower = line.lower()
            service_lower = service_name.lower()

            # Проверяем, содержит ли строка название услуги
            if service_lower in line_lower or any(word in line_lower for word in service_lower.split()):

                # Ищем цену в этой строке
                price_patterns = [
                    r'(\d+(?:\s*-\s*\d+)?)\s*(?:₽|руб)',  # 1500 ₽ или 1500-2000 ₽
                    r'(\d+(?:\s*-\s*\d+)?)\s*р\.',        # 1500 р.
                    r'от\s*(\d+)\s*(?:₽|руб)',            # от 1500 ₽
                    r'стоимость[:\s]*(\d+)\s*(?:₽|руб)',  # стоимость: 1500 ₽
                ]

                price = None
                for pattern in price_patterns:
                    price_match = re.search(pattern, line, re.IGNORECASE)
                    if price_match:
                        price_str = price_match.group(1)
                        # Обрабатываем диапазон цен
                        if '-' in price_str:
                            price_parts = price_str.split('-')
                            try:
                                price = int(price_parts[0].strip())  # Берем минимальную цену
                            except ValueError:
                                continue
                        else:
                            try:
                                price = int(price_str)
                            except ValueError:
                                continue
                        break

                # Ищем длительность в этой строке или соседних
                duration = None
                duration_patterns = [
                    r'(\d+)\s*мин',                       # 60 мин
                    r'длительность[:\s]*(\d+)\s*мин',     # длительность: 60 мин
                    r'время[:\s]*(\d+)\s*мин',            # время: 60 мин
                ]

                # Проверяем текущую строку и несколько соседних
                search_lines = lines[max(0, i-2):min(len(lines), i+3)]
                for search_line in search_lines:
                    for pattern in duration_patterns:
                        duration_match = re.search(pattern, search_line, re.IGNORECASE)
                        if duration_match:
                            try:
                                duration = int(duration_match.group(1))
                                break
                            except ValueError:
                                continue
                    if duration:
                        break

                # Извлекаем точное название услуги из строки
                service_title = service_name

                # Пытаемся найти более точное название услуги в строке
                if line.startswith('###'):
                    # Заголовок услуги
                    service_title = line.replace('###', '').strip()
                elif '-' in line and any(char.isdigit() for char in line):
                    # Строка вида "- Название услуги - 1500 ₽"
                    parts = line.split('-')
                    if len(parts) >= 2:
                        potential_title = parts[1].strip()
                        if potential_title and not potential_title.isdigit():
                            service_title = potential_title

                if price:
                    return {
                        "title": service_title,
                        "price": price,
                        "duration": duration or self._estimate_service_duration(service_title, ""),
                        "description": ""
                    }

        return None

    def _normalize_category_name(self, category: str) -> str:
        """Нормализация названия категории"""
        category_map = {
            'services_manicure': 'Маникюр',
            'services_hair': 'Парикмахерские услуги',
            'services_cosmetology': 'Косметология',
            'services_eyebrows': 'Брови',
            'services_eyelashes': 'Ресницы',
            'services_injections': 'Инъекционная косметология',
            'services_depilation': 'Депиляция',
            'services_other': 'Другие услуги'
        }

        # Убираем расширение .md и путь
        clean_category = category.replace('.md', '').split('/')[-1]
        return category_map.get(clean_category, clean_category.replace('_', ' ').title())

    async def handle_get_staff(self, **kwargs) -> Dict[str, Any]:
        """Tool handler: получить список мастеров из базы знаний Qdrant"""
        logger.info("YTH_HGT: Обработка tool: get_staff")
        logger.info(f"YTH_HGT: Параметры вызова: {kwargs}")
        logger.info(f"YTH_HGT: Полные параметры kwargs: {json.dumps(kwargs, ensure_ascii=False, indent=2) if kwargs else 'None'}")

        try:
            logger.info("YTH_HGT: Поиск мастеров в базе знаний Qdrant...")

            # Получаем точки с категорией "specialists" напрямую из Qdrant без embeddings
            try:
                scroll_result = self.embedding_service.qdrant_client.scroll(
                    collection_name=self.embedding_service.collection_name,
                    scroll_filter={
                        "must": [
                            {"key": "category", "match": {"value": "specialists"}}
                        ]
                    },
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
                search_results = scroll_result[0]
                logger.info(f"YTH_HGT: Найдено {len(search_results)} точек с категорией specialists")
            except Exception as e:
                logger.warning(f"YTH_HGT: Ошибка при поиске по категории, пробуем семантический поиск: {e}")
                logger.warning(f"YTH_HGT: Полная информация об ошибке: {str(e)}", exc_info=True)
                # Fallback на семантический поиск если не работает фильтр
                search_results = await self.embedding_service.search_similar(
                    query="Севиль Бамматова Джамиля Хункаева Мадина Багатырова специалисты команда мастера",
                    limit=10
                )

            staff_list = []
            processed_staff = set()  # Для исключения дубликатов

            for result in search_results:
                content = result.payload.get("content", "")
                full_text = result.payload.get("full_text", "")

                # Используем full_text если content пустой
                text_to_parse = content if content else full_text

                if not text_to_parse:
                    logger.warning("YTH_HGT: Пустой контент в результате поиска")
                    continue

                # Парсим мастеров из контента
                staff_lines = text_to_parse.split('\n')

                # Список известных имен мастеров для фильтрации
                known_staff_names = ['Севиль Бамматова', 'Джамиля Хункаева', 'Мадина Багатырова']

                for line in staff_lines:
                    line = line.strip()

                    # Ищем заголовки с именами мастеров (формат: ### Имя Фамилия)
                    if line.startswith('### '):
                        name = line.replace('### ', '').strip()
                        # Проверяем, что это действительно имя мастера
                        if name in known_staff_names and name not in processed_staff:
                            processed_staff.add(name)
                            staff_list.append({
                                "id": len(staff_list) + 1,
                                "name": name,
                                "specialization": "Специалист"  # Базовая специализация
                            })

                    # Ищем строки со специализацией (формат: **Специализация:** Название)
                    elif '**Специализация:**' in line:
                        specialization = line.split('**Специализация:**', 1)[1].strip()
                        # Обновляем специализацию последнего добавленного мастера
                        if staff_list:
                            staff_list[-1]["specialization"] = specialization

                    # Дополнительно ищем в формате списка (- **Имя** — специализация)
                    elif line.startswith('- **') and '**' in line and '—' in line:
                        parts = line.split('**')
                        if len(parts) >= 3:
                            name = parts[1].strip()
                            if name in known_staff_names and name not in processed_staff:
                                processed_staff.add(name)
                                # Извлекаем специализацию после —
                                rest = line.split('—', 1)
                                specialization = rest[1].strip() if len(rest) > 1 else "Специалист"
                                staff_list.append({
                                    "id": len(staff_list) + 1,
                                    "name": name,
                                    "specialization": specialization
                                })

            logger.info(f"YTH_HGT: Найдено {len(staff_list)} мастеров в базе знаний")
            logger.info(f"YTH_HGT: Успешно обработано {len(staff_list)} мастеров")
            logger.info(f"YTH_HGT: Первые 3 мастера: {staff_list[:3] if len(staff_list) > 3 else staff_list}")
            logger.info(f"YTH_HGT: Полный список сотрудников: {json.dumps(staff_list, ensure_ascii=False, indent=2)}")

            return {"staff": staff_list, "success": True}
        except Exception as e:
            logger.error(f"YTH_HGT: Ошибка в tool get_staff: {e}")
            logger.error(f"YTH_HGT: Тип ошибки: {type(e).__name__}")
            logger.error(f"YTH_HGT: Полная информация об ошибке: {str(e)}", exc_info=True)
            return {"error": str(e), "success": False}

    async def handle_find_service_by_name(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """Tool handler: найти услугу по названию в базе знаний Qdrant"""
        logger.info(f"YTH_HFSBN: Обработка tool: find_service_by_name('{service_name}')")
        logger.info(f"YTH_HFSBN: Параметры вызова: service_name='{service_name}', kwargs={kwargs}")
        logger.info(f"YTH_HFSBN: Полные параметры kwargs: {json.dumps(kwargs, ensure_ascii=False, indent=2) if kwargs else 'None'}")

        try:
            logger.info(f"YTH_HFSBN: Ищем услугу '{service_name}' в базе знаний Qdrant...")

            # Сначала используем семантический поиск через embeddings
            search_results = []

            try:
                logger.info(f"YTH_HFSBN: Выполняем семантический поиск для '{service_name}'...")
                search_results = await self.embedding_service.search_similar(
                    query=f"услуга {service_name} цена стоимость длительность",
                    limit=10
                )
                logger.info(f"YTH_HFSBN: Найдено {len(search_results)} результатов через семантический поиск")
            except Exception as e:
                logger.warning(f"YTH_HFSBN: Ошибка при семантическом поиске: {e}")
                logger.warning(f"YTH_HFSBN: Полная информация об ошибке: {str(e)}", exc_info=True)

            # Если семантический поиск не дал результатов, используем fallback через scroll
            if not search_results:
                logger.info("YTH_HFSBN:  Семантический поиск не дал результатов, пробуем поиск через scroll...")
                service_categories = ["services", "pricing", "cosmetology", "hair", "manicure", "eyebrows", "eyelashes", "depilation", "injections", "other"]

                try:
                    for category in service_categories:
                        scroll_result = self.embedding_service.qdrant_client.scroll(
                            collection_name=self.embedding_service.collection_name,
                            scroll_filter={
                                "must": [
                                    {"key": "category", "match": {"value": category}}
                                ]
                            },
                            limit=100,
                            with_payload=True,
                            with_vectors=False
                        )
                        # Фильтруем результаты по названию услуги
                        for point in scroll_result[0]:
                            content = point.payload.get("content", "")
                            if service_name.lower() in content.lower():
                                # Создаем объект с атрибутом score для совместимости
                                from types import SimpleNamespace
                                point_with_score = SimpleNamespace(
                                    payload=point.payload,
                                    score=0.9  # Фиктивный score для локального поиска
                                )
                                search_results.append(point_with_score)
                                if len(search_results) >= 5:
                                    break
                        if len(search_results) >= 5:
                            break

                    logger.info(f"YTH_HFSBN:  Найдено {len(search_results)} результатов через scroll")
                except Exception as e:
                    logger.warning(f"YTH_HFSBN:  Ошибка при поиске через scroll: {e}")
                    search_results = []

            best_match = None
            best_score = 0

            for result in search_results:
                content = result.payload.get("content", "")
                score = result.score

                logger.info(f"YTH_HFSBN:  Анализируем результат со score {score:.3f}")

                # Улучшенный поиск услуги в контенте - ищем как точное совпадение, так и частичное
                service_found = False
                service_title = service_name

                # Проверяем точное совпадение
                if service_name.lower() in content.lower():
                    service_found = True
                else:
                    # Проверяем частичное совпадение по словам
                    service_words = service_name.lower().split()
                    content_lower = content.lower()
                    matching_words = sum(1 for word in service_words if word in content_lower)
                    if matching_words >= len(service_words) * 0.5:  # Минимум 50% слов должны совпадать
                        service_found = True

                if service_found:
                    logger.info(f"YTH_HFSBN:  Услуга найдена в контенте")

                    # Улучшенный поиск цены и длительности
                    parsed_service = self._parse_service_from_content(content, service_name)

                    if parsed_service and parsed_service.get("price", 0) > 0:
                        logger.info(f"YTH_HFSBN:  Найдена цена: {parsed_service['price']} ₽")
                        best_match = {
                            "id": hash(service_name) % 10000,
                            "title": parsed_service["title"],
                            "price": parsed_service["price"],
                            "price_display": f"{parsed_service['price']} ₽",
                            "duration": parsed_service["duration"],
                            "category": self._normalize_category_name(result.payload.get("file_path", "Общие")),
                            "description": parsed_service.get("description", "")
                        }
                        best_score = score
                        break
                    elif score > best_score:
                        # Если цена не найдена, но услуга упоминается
                        duration = self._estimate_service_duration(service_name, result.payload.get("file_path", ""))
                        best_match = {
                            "id": hash(service_name) % 10000,
                            "title": service_name,
                            "price": 0,
                            "price_display": "Цена по запросу",
                            "duration": duration,
                            "category": self._normalize_category_name(result.payload.get("file_path", "Общие")),
                            "description": ""
                        }
                        best_score = score

            if best_match:
                logger.info(f"YTH_HFSBN:  Tool find_service_by_name: найдена услуга '{best_match['title']}'")
                logger.info(f"YTH_HFSBN:  Детали услуги: {best_match}")
                return {"service": best_match, "found": True, "success": True}
            else:
                logger.info(f"YTH_HFSBN:  Tool find_service_by_name: услуга '{service_name}' не найдена")
                return {"service": None, "found": False, "success": True}
        except Exception as e:
            logger.error(f"YTH_HFSBN:  Ошибка в tool find_service_by_name: {e}")
            logger.error(f"YTH_HFSBN:  Тип ошибки: {type(e).__name__}")
            return {"error": str(e), "success": False}

    async def handle_find_staff_by_name(self, staff_name: str, **kwargs) -> Dict[str, Any]:
        """Tool handler: найти мастера по имени в базе знаний Qdrant"""
        logger.info(f"YTH_HFSN: Обработка tool: find_staff_by_name('{staff_name}')")
        logger.info(f"YTH_HFSN: Параметры вызова: staff_name='{staff_name}', kwargs={kwargs}")
        logger.info(f"YTH_HFSN: Полные параметры kwargs: {json.dumps(kwargs, ensure_ascii=False, indent=2) if kwargs else 'None'}")

        # Проверяем на пустое имя
        if not staff_name or not staff_name.strip():
            logger.info("YTH_HFSN:  Пустое имя мастера, возвращаем пустой результат")
            return {"staff": None, "found": False, "success": True}

        try:
            logger.info(f"YTH_HFSN:  Ищем мастера '{staff_name}' в базе знаний Qdrant...")

            # Сначала пробуем найти без embeddings через scroll с фильтром по категории specialists
            search_results = []

            try:
                scroll_result = self.embedding_service.qdrant_client.scroll(
                    collection_name=self.embedding_service.collection_name,
                    scroll_filter={
                        "must": [
                            {"key": "category", "match": {"value": "specialists"}}
                        ]
                    },
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )

                # Фильтруем результаты по имени мастера
                for point in scroll_result[0]:
                    content = point.payload.get("content", "")
                    if staff_name.lower() in content.lower():
                        # Создаем объект с атрибутом score для совместимости
                        from types import SimpleNamespace
                        point_with_score = SimpleNamespace(
                            payload=point.payload,
                            score=0.9  # Фиктивный score для локального поиска
                        )
                        search_results.append(point_with_score)
                        if len(search_results) >= 5:
                            break

                logger.info(f"YTH_HFSN:  Найдено {len(search_results)} результатов без embeddings")
            except Exception as e:
                logger.warning(f"YTH_HFSN:  Ошибка при поиске без embeddings, пробуем семантический поиск: {e}")
                # Fallback на семантический поиск
                search_results = await self.embedding_service.search_similar(
                    query=f"мастер {staff_name} специализация услуги",
                    limit=5
                )

            best_match = None
            best_score = 0

            for result in search_results:
                content = result.payload.get("content", "")
                score = result.score

                # Ищем упоминание мастера в контенте
                if staff_name.lower() in content.lower():
                    # Пытаемся найти специализацию
                    lines = content.split('\n')
                    for line in lines:
                        if staff_name.lower() in line.lower():
                            # Извлекаем специализацию из строки
                            if '-' in line:
                                parts = line.split('-', 1)
                                if len(parts) == 2:
                                    specialization = parts[1].strip()
                                    best_match = {
                                        "id": hash(staff_name) % 10000,  # Генерируем стабильный ID
                                        "name": staff_name,
                                        "specialization": specialization
                                    }
                                    best_score = score
                                    break

                    if not best_match and score > best_score:
                        # Если специализация не найдена, но мастер упоминается
                        best_match = {
                            "id": hash(staff_name) % 10000,
                            "name": staff_name,
                            "specialization": "Универсальный мастер"
                        }
                        best_score = score

            if best_match:
                logger.info(f"YTH_HFSN:  Tool find_staff_by_name: найден мастер '{best_match['name']}'")
                logger.info(f"YTH_HFSN:  Детали мастера: {best_match}")
                return {"staff": best_match, "found": True, "success": True}
            else:
                logger.info(f"YTH_HFSN:  Tool find_staff_by_name: мастер '{staff_name}' не найден")
                return {"staff": None, "found": False, "success": True}
        except Exception as e:
            logger.error(f"YTH_HFSN:  Ошибка в tool find_staff_by_name: {e}")
            logger.error(f"YTH_HFSN:  Тип ошибки: {type(e).__name__}")
            return {"error": str(e), "success": False}

    async def handle_get_available_slots(self, service_ids: List[int], date_from: str,
                                       date_to: str, staff_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Tool handler: получить свободные слоты"""
        logger.info(f"YTH_HGAS: Обработка tool: get_available_slots(services={service_ids}, "
                   f"from={date_from}, to={date_to}, staff={staff_id})")
        logger.info(f"YTH_HGAS: Параметры вызова: service_ids={service_ids}, date_from='{date_from}', "
                   f"date_to='{date_to}', staff_id={staff_id}, kwargs={kwargs}")
        logger.info(f"YTH_HGAS: Полные параметры kwargs: {json.dumps(kwargs, ensure_ascii=False, indent=2) if kwargs else 'None'}")

        try:
            # Парсим даты
            logger.info("YTH_HGAS:  Парсим даты...")
            date_from_dt = datetime.fromisoformat(date_from)
            date_to_dt = datetime.fromisoformat(date_to)
            logger.info(f"YTH_HGAS:  Дата начала: {date_from_dt}, Дата окончания: {date_to_dt}")

            # Если указан конкретный мастер и одна услуга, используем новые методы
            if staff_id and len(service_ids) == 1:
                logger.info("YTH_HGAS:  Используем новые методы get_available_days + get_available_times")
                try:
                    slots = await self.yclients.get_available_slots_for_staff(
                        staff_id=staff_id,
                        service_id=service_ids[0],
                        date_from=date_from_dt,
                        date_to=date_to_dt
                    )
                except Exception as e:
                    # Проверяем, является ли это ошибкой недоступности мастера
                    if hasattr(e, 'error_code') and e.error_code == 'STAFF_UNAVAILABLE':
                        logger.warning(f"YTH_HGAS:  Мастер {staff_id} недоступен для услуги {service_ids[0]}")

                        # Получаем альтернативных мастеров
                        alternative_masters = await self._get_alternative_masters(service_ids[0])

                        return {
                            "slots": [],
                            "total_found": 0,
                            "success": True,
                            "error": str(e),
                            "error_code": "STAFF_UNAVAILABLE",
                            "staff_id": staff_id,
                            "service_id": service_ids[0],
                            "suggestion": "Попробуйте выбрать другого мастера или другую услугу",
                            "alternative_masters": alternative_masters
                        }
                    else:
                        # Для других ошибок - пробрасываем дальше
                        raise
            else:
                logger.info("YTH_HGAS:  Используем старый метод get_available_slots()...")
                slots = await self.yclients.get_available_slots(
                    service_ids=service_ids,
                    date_from=date_from_dt,
                    date_to=date_to_dt,
                    staff_id=staff_id
                )
            logger.info(f"YTH_HGAS:  Получено {len(slots) if slots else 0} слотов от Yclients")

            result = [
                {
                    "start": slot.start.isoformat(),
                    "end": slot.end.isoformat(),
                    "staff_id": slot.staff_id,
                    "available": slot.available
                }
                for slot in slots[:20]  # Ограничиваем количество для экономии токенов
            ]

            logger.info(f"YTH_HGAS:  Tool get_available_slots: успешно обработано {len(slots)} слотов (показано {len(result)})")
            if result:
                logger.info(f"YTH_HGAS:  Первые 3 слота: {result[:3]}")

            return {"slots": result, "total_found": len(slots), "success": True}
        except Exception as e:
            logger.error(f"YTH_HGAS:  Ошибка в tool get_available_slots: {e}")
            logger.error(f"YTH_HGAS:  Тип ошибки: {type(e).__name__}")
            return {"error": str(e), "success": False}

    async def _get_alternative_masters(self, service_id: int) -> List[Dict[str, Any]]:
        """
        Получить список альтернативных мастеров для услуги

        Args:
            service_id: ID услуги для которой ищем мастеров

        Returns:
            Список мастеров с их данными
        """
        try:
            logger.info(f"YTH_GAM:  Поиск альтернативных мастеров для услуги {service_id}")

            # Получаем всех мастеров из базы знаний
            masters_result = await self.handle_get_staff()

            if not masters_result.get('success', False):
                logger.warning("YTH_GAM:  Не удалось получить список мастеров")
                return []

            all_masters = masters_result.get('staff', [])
            logger.info(f"YTH_GAM:  Найдено мастеров в базе знаний: {len(all_masters)}")

            # Возвращаем первых 3-5 мастеров как альтернативы
            # TODO: В будущем можно добавить логику фильтрации по специализации
            alternative_masters = all_masters[:5]

            logger.info(f"YTH_GAM:  Подготовлено {len(alternative_masters)} альтернативных мастеров")
            return alternative_masters

        except Exception as e:
            logger.error(f"YTH_GAM:  Ошибка при получении альтернативных мастеров: {e}")
            return []

    async def handle_create_booking(self, phone: str, fullname: str, service_ids: List[int],
                                  staff_id: int, booking_datetime: str, email: Optional[str] = None,
                                  comment: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Tool handler: создать запись в локальной базе данных"""
        logger.info(f"YTH_HCB: Обработка tool: create_booking(client='{fullname}', phone='{phone}', "
                   f"services={service_ids}, staff={staff_id}, datetime='{booking_datetime}')")
        logger.info(f"YTH_HCB: Параметры вызова: phone='{phone}', fullname='{fullname}', service_ids={service_ids}, "
                   f"staff_id={staff_id}, booking_datetime='{booking_datetime}', email='{email}', "
                   f"comment='{comment}', kwargs={kwargs}")
        logger.info(f"YTH_HCB: Полные параметры kwargs: {json.dumps(kwargs, ensure_ascii=False, indent=2) if kwargs else 'None'}")

        try:
            # Парсим дату
            logger.info("YTH_HCB:  Парсим дату бронирования...")
            booking_dt = datetime.fromisoformat(booking_datetime.replace('Z', '+00:00'))
            logger.info(f"YTH_HCB:  Дата бронирования: {booking_dt}")

            # Сохраняем запись в локальную базу данных
            logger.info("YTH_HCB:  Сохраняем запись в локальную базу данных...")

            with SessionLocal() as db:
                # Проверяем/создаем клиента
                client = None

                # Сначала пытаемся найти клиента по telegram_id
                if self.telegram_id:
                    client = db.query(Client).filter(Client.telegram_id == str(self.telegram_id)).first()

                # Если не нашли по telegram_id, ищем по телефону
                if not client and phone:
                    # Нормализуем телефон для поиска
                    normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
                    client = db.query(Client).filter(Client.phone.contains(normalized_phone[-10:])).first()

                # Если клиент не найден, создаем нового
                if not client:
                    client = Client(
                        telegram_id=str(self.telegram_id) if self.telegram_id else f"phone_{phone}",
                        first_name=fullname.split()[0] if fullname else "Клиент",
                        last_name=' '.join(fullname.split()[1:]) if len(fullname.split()) > 1 else None,
                        phone=phone
                    )
                    db.add(client)
                    db.commit()
                    db.refresh(client)
                    logger.info(f"YTH_HCB:  Создан новый клиент ID: {client.id} для {fullname} ({phone})")
                else:
                    # Обновляем данные клиента если нужно
                    updated = False
                    if phone and not client.phone:
                        client.phone = phone
                        updated = True
                    if fullname and not client.first_name:
                        client.first_name = fullname.split()[0] if fullname else None
                        client.last_name = ' '.join(fullname.split()[1:]) if len(fullname.split()) > 1 else None
                        updated = True
                    if updated:
                        db.commit()
                    logger.info(f"YTH_HCB:  Используем существующего клиента ID: {client.id}")

                # Получаем названия услуг из service_ids (для отображения)
                service_names = []
                if service_ids:
                    # Получаем реальные названия услуг
                    services_data = await self._get_services_from_api()
                    services_dict = {s.get('id'): s.get('title', f'Услуга #{s.get("id")}') for s in services_data}

                    for service_id in service_ids:
                        service_name = services_dict.get(service_id, f"Услуга #{service_id}")
                        service_names.append(service_name)
                        logger.info(f"YTH_HCB:  Услуга ID {service_id} -> '{service_name}'")

                # Получаем реальное имя мастера из staff_id
                staff_name = f"Мастер #{staff_id}"
                try:
                    # Пытаемся получить реальное имя мастера из YClients API
                    staff_data = await self.yclients.get_staff()
                    if staff_data and 'data' in staff_data:
                        for staff_member in staff_data['data']:
                            if staff_member.get('id') == staff_id:
                                staff_name = staff_member.get('name', f"Мастер #{staff_id}")
                                logger.info(f"YTH_HCB:  Мастер ID {staff_id} -> '{staff_name}'")
                                break
                except Exception as e:
                    logger.warning(f"YTH_HCB:  Не удалось получить имя мастера ID {staff_id}: {e}")
                    # Оставляем заглушку

                # Создаем запись о встрече
                # Теперь client всегда должен существовать
                if not client or not client.id:
                    raise ValueError("Не удалось создать или найти клиента")

                appointment = Appointment(
                    client_id=client.id,  # Теперь client_id всегда будет заполнен
                    service_ids=json.dumps(service_ids) if service_ids else None,  # Сохраняем ID услуг как JSON
                    staff_id=staff_id,  # Сохраняем ID мастера
                    service_name=", ".join(service_names) if service_names else "Услуга",
                    master_name=staff_name,
                    appointment_datetime=booking_dt,
                    duration_minutes=60,  # Стандартная длительность
                    status="scheduled"
                )
                db.add(appointment)
                db.commit()
                db.refresh(appointment)

                logger.info(f"YTH_HCB:  Запись успешно создана в локальной БД с ID: {appointment.id}")

                result = {
                    "success": True,
                    "record_id": appointment.id,
                    "client_name": fullname,
                    "phone": phone,
                    "services": service_names,
                    "master": staff_name,
                    "datetime": booking_dt.isoformat(),
                    "status": "scheduled",
                    "message": "Запись успешно создана в системе"
                }

                logger.info(f"YTH_HCB:  Детали записи: {result}")
                return {"booking": result, "success": True}

        except Exception as e:
            logger.error(f"YTH_HCB:  Ошибка в tool create_booking: {e}")
            logger.error(f"YTH_HCB:  Тип ошибки: {type(e).__name__}")
            return {"error": str(e), "success": False}

    async def handle_get_available_days(self, staff_id: int, service_id: int, **kwargs) -> Dict[str, Any]:
        """Tool handler: получить доступные дни для записи к сотруднику"""
        logger.info(f"YTH_HGAD:  Обработка tool: get_available_days(staff_id={staff_id}, service_id={service_id})")

        try:
            logger.info("YTH_HGAD:  Вызываем yclients.get_available_days()...")
            booking_days = await self.yclients.get_available_days(staff_id=staff_id, service_id=service_id)

            # Проверяем на ошибку недоступности мастера
            if 'error' in booking_days:
                error_code = booking_days.get('error_code')
                if error_code == 'STAFF_UNAVAILABLE':
                    logger.warning(f"YTH_HGAD:  Мастер {staff_id} недоступен для услуги {service_id}")
                    return {
                        "error": booking_days['error'],
                        "error_code": "STAFF_UNAVAILABLE",
                        "staff_id": staff_id,
                        "service_id": service_id,
                        "suggestion": "Попробуйте выбрать другого мастера или другую услугу",
                        "success": False
                    }
                else:
                    return {
                        "error": booking_days['error'],
                        "success": False
                    }

            days = booking_days['data'].get('booking_dates', [])
            logger.info(f"YTH_HGAD:  Получено {len(days)} доступных дней")

            # Преобразуем timestamps в читаемые даты для удобства
            readable_days = []
            for day in days:
                try:
                    if isinstance(day, (int, float)):
                        readable_days.append({
                            "timestamp": day,
                            "date": datetime.fromtimestamp(day).strftime('%Y-%m-%d'),
                            "day_of_week": datetime.fromtimestamp(day).strftime('%A')
                        })
                    elif isinstance(day, str):
                        readable_days.append({
                            "date": day,
                            "timestamp": None
                        })
                except Exception as e:
                    logger.warning(f"YTH_HGAD:  Ошибка обработки даты {day}: {e}")
                    continue

            logger.info(f"YTH_HGAD:  Tool get_available_days: успешно обработано {len(days)} дней")
            return {
                "days": readable_days[:10],  # Ограничиваем для экономии токенов
                "total_found": len(days),
                "success": True
            }
        except Exception as e:
            logger.error(f"YTH_HGAD:  Ошибка в tool get_available_days: {e}")
            return {"error": str(e), "success": False}

    async def handle_get_available_times(self, staff_id: int, service_id: int, day: str, **kwargs) -> Dict[str, Any]:
        """Tool handler: получить доступные временные слоты на конкретную дату"""
        logger.info(f"YTH_HGAT:  Обработка tool: get_available_times(staff_id={staff_id}, service_id={service_id}, day='{day}')")

        try:
            logger.info("YTH_HGAT:  Вызываем yclients.get_available_times()...")
            time_slots = await self.yclients.get_available_times(staff_id=staff_id, service_id=service_id, day=day)

            slots = time_slots['data']
            logger.info(f"YTH_HGAT:  Получено {len(slots)} временных слотов")

            # Форматируем слоты для удобства чтения
            formatted_slots = []
            for slot in slots:
                try:
                    formatted_slot = {
                        "time": slot.get('time', ''),
                        "duration_seconds": slot.get('seance_length', 3600),
                        "duration_minutes": slot.get('seance_length', 3600) // 60,
                        "datetime": slot.get('datetime', 0)
                    }

                    # Добавляем читаемое время окончания
                    if slot.get('datetime'):
                        start_time = datetime.fromtimestamp(slot['datetime'])
                        end_time = start_time + timedelta(seconds=slot.get('seance_length', 3600))
                        formatted_slot['start_datetime'] = start_time.strftime('%Y-%m-%d %H:%M')
                        formatted_slot['end_datetime'] = end_time.strftime('%Y-%m-%d %H:%M')

                    formatted_slots.append(formatted_slot)
                except Exception as e:
                    logger.warning(f"YTH_HGAT:  Ошибка форматирования слота {slot}: {e}")
                    continue

            logger.info(f"YTH_HGAT:  Tool get_available_times: успешно обработано {len(slots)} слотов")
            return {
                "slots": formatted_slots[:15],  # Ограничиваем для экономии токенов
                "total_found": len(slots),
                "success": True
            }
        except Exception as e:
            logger.error(f"YTH_HGAT: Ошибка в tool get_available_times: {e}")
            logger.error(f"YTH_HGAT: Полная информация об ошибке: {str(e)}", exc_info=True)
            return {"error": str(e), "success": False}
