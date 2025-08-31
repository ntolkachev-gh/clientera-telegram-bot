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
        logger.info("YTD_GTS:   get_services - получение списка услуг для клиента (без ID)")
        logger.info("YTD_GTS:   get_services_with_id - получение списка услуг с ID для записи")
        logger.info("YTD_GTS:   get_staff - получение списка мастеров")

        logger.info("YTD_GTS:   get_available_slots - получение свободных слотов")
        logger.info("YTD_GTS:   get_available_days - получение доступных дней")
        logger.info("YTD_GTS:   get_available_times - получение временных слотов")
        logger.info("YTH_GTS:   create_booking - создание записи")

        tools = [
            YclientsToolsDefinition._get_services_tool(),
            YclientsToolsDefinition._get_services_with_id_tool(),
            YclientsToolsDefinition._get_staff_tool(),
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
        """Схема tool для получения списка услуг (только название и длительность)"""
        return {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": "Получить список доступных услуг салона для показа клиенту (только название, цена и длительность, без ID). Используй этот tool когда нужно показать клиенту какие услуги доступны.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    @staticmethod
    def _get_services_with_id_tool() -> Dict[str, Any]:
        """Схема tool для получения списка услуг с ID для создания записи"""
        return {
            "type": "function",
            "function": {
                "name": "get_services_with_id",
                "description": "Получить список доступных услуг салона с ID для создания записи. Используй этот tool только когда нужно получить ID услуг для создания записи через create_booking.",
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
            "get_services_with_id": self.handle_get_services_with_id,
            "get_staff": self.handle_get_staff,
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
        """Tool handler: получить список услуг для показа клиенту (без ID)"""
        logger.info("YTH_HGS: Обработка tool: get_services (без ID)")
        logger.info(f"YTH_HGS: Параметры вызова: {kwargs}")

        try:
            logger.info("YTH_HGS: Получение услуг для показа клиенту...")

            # Получаем услуги из API
            services_full = await self._get_services_from_api()

            # Убираем ID из данных для клиента
            services_for_client = []
            for service in services_full:
                client_service = {
                    "title": service.get("title"),
                    "price": service.get("price"),
                    "price_display": service.get("price_display"),
                    "duration": service.get("duration"),
                    "category": service.get("category"),
                    "specialist": service.get("specialist"),
                    "description": service.get("description")
                }
                services_for_client.append(client_service)

            logger.info(f"YTH_HGS: Найдено {len(services_for_client)} услуг для показа клиенту")

            return {
                "services": services_for_client,
                "total_count": len(services_for_client),
                "success": True
            }

        except Exception as e:
            logger.error(f"YTH_HGS: Ошибка в tool get_services: {e}")
            return {"error": str(e), "success": False}

    async def handle_get_services_with_id(self, **kwargs) -> Dict[str, Any]:
        """Tool handler: получить список услуг с ID для создания записи"""
        logger.info("YTH_HGSWI: Обработка tool: get_services_with_id (с ID)")
        logger.info(f"YTH_HGSWI: Параметры вызова: {kwargs}")

        try:
            logger.info("YTH_HGSWI: Получение услуг с ID для создания записи...")

            # Получаем полные данные услуг из API (с ID)
            services_with_id = await self._get_services_from_api()

            logger.info(f"YTH_HGSWI: Найдено {len(services_with_id)} услуг с ID")

            if services_with_id:
                logger.info(f"YTH_HGSWI: Первые 3 услуги с ID: {services_with_id[:3]}")

            return {
                "services": services_with_id,
                "total_count": len(services_with_id),
                "success": True
            }

        except Exception as e:
            logger.error(f"YTH_HGSWI: Ошибка в tool get_services_with_id: {e}")
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
        """Tool handler: получить список мастеров из YClients API"""
        logger.info("YTH_HGT: Обработка tool: get_staff")
        logger.info(f"YTH_HGT: Параметры вызова: {kwargs}")

        try:
            logger.info("YTH_HGT: Получение списка мастеров из YClients API...")

            # Получаем список мастеров через YClients API
            if not self.yclients:
                logger.error("YTH_HGT: YClients клиент недоступен")
                return {"error": "YClients клиент недоступен", "success": False}

            # Получаем мастеров через API
            staff_list = await self.yclients.get_staff(force_refresh=True, use_real_api=True)

            # Преобразуем в формат для ответа
            staff_response = []
            for staff in staff_list:
                if hasattr(staff, 'id'):  # Если это объект Staff
                    staff_response.append({
                        "id": staff.id,
                        "name": staff.name,
                        "specialization": staff.specialization
                    })
                else:  # Если это словарь
                    staff_response.append({
                        "id": staff.get("id"),
                        "name": staff.get("name"),
                        "specialization": staff.get("specialization")
                    })

            logger.info(f"YTH_HGT: Найдено {len(staff_response)} мастеров в API")
            logger.info(f"YTH_HGT: Полный список сотрудников: {json.dumps(staff_response, ensure_ascii=False, indent=2)}")

            return {"staff": staff_response, "success": True}
        except Exception as e:
            logger.error(f"YTH_HGT: Ошибка в tool get_staff: {e}")
            logger.error(f"YTH_HGT: Полная информация об ошибке: {str(e)}", exc_info=True)
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

    def _validate_service_ids(self, service_ids: List[int]) -> Dict[str, Any]:
        """
        Валидация service_ids

        Returns:
            {"valid": bool, "error": str} - результат валидации
        """
        if not service_ids:
            return {"valid": False, "error": "service_ids не может быть пустым"}

        if not isinstance(service_ids, list):
            return {"valid": False, "error": f"service_ids должен быть списком, получен {type(service_ids)}"}

        # Проверяем что все элементы - целые числа
        for i, service_id in enumerate(service_ids):
            if not isinstance(service_id, int):
                return {"valid": False, "error": f"service_ids[{i}] должен быть целым числом, получен {type(service_id)}: {service_id}"}

            if service_id <= 0:
                return {"valid": False, "error": f"service_ids[{i}] должен быть больше 0, получен: {service_id}"}

            # Проверяем что ID похож на реальный YClients ID (обычно 8-значные)
            if service_id < 1000000:  # Меньше 7 цифр - подозрительно
                logger.warning(f"YTH_VSI: Подозрительный service_id {service_id} - слишком маленький для YClients")

        # Проверяем разумное количество услуг (не больше 10 за раз)
        if len(service_ids) > 10:
            return {"valid": False, "error": f"Слишком много услуг за раз: {len(service_ids)}, максимум 10"}

        return {"valid": True, "error": None}

    def _validate_staff_id(self, staff_id: int) -> Dict[str, Any]:
        """
        Валидация staff_id

        Returns:
            {"valid": bool, "error": str} - результат валидации
        """
        if not isinstance(staff_id, int):
            return {"valid": False, "error": f"staff_id должен быть целым числом, получен {type(staff_id)}: {staff_id}"}

        if staff_id <= 0:
            return {"valid": False, "error": f"staff_id должен быть больше 0, получен: {staff_id}"}

        # Проверяем что ID похож на реальный YClients ID
        if staff_id < 1000000:  # Меньше 7 цифр - подозрительно
            logger.warning(f"YTH_VSI: Подозрительный staff_id {staff_id} - слишком маленький для YClients")

        return {"valid": True, "error": None}

    def _validate_booking_datetime(self, booking_datetime: str) -> Dict[str, Any]:
        """
        Валидация booking_datetime

        Returns:
            {"valid": bool, "error": str, "parsed_datetime": datetime} - результат валидации
        """
        if not booking_datetime or not isinstance(booking_datetime, str):
            return {"valid": False, "error": "booking_datetime должен быть непустой строкой"}

        try:
            # Парсим дату с поддержкой разных форматов
            booking_dt = datetime.fromisoformat(booking_datetime.replace('Z', '+00:00'))

            # Проверяем что дата в будущем
            now = datetime.now()
            if booking_dt <= now:
                return {"valid": False, "error": f"Дата записи должна быть в будущем. Получена: {booking_dt}, сейчас: {now}"}

            # Проверяем что дата не слишком далеко в будущем (например, не больше года)
            max_future = now + timedelta(days=365)
            if booking_dt > max_future:
                return {"valid": False, "error": f"Дата записи слишком далеко в будущем: {booking_dt}"}

            return {"valid": True, "error": None, "parsed_datetime": booking_dt}

        except ValueError as e:
            return {"valid": False, "error": f"Некорректный формат даты '{booking_datetime}': {str(e)}"}

    def _validate_contact_info(self, phone: str, fullname: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Валидация контактной информации

        Returns:
            {"valid": bool, "error": str} - результат валидации
        """
        if not phone or not isinstance(phone, str) or len(phone.strip()) == 0:
            return {"valid": False, "error": "Телефон не может быть пустым"}

        if not fullname or not isinstance(fullname, str) or len(fullname.strip()) == 0:
            return {"valid": False, "error": "Имя клиента не может быть пустым"}

        # Базовая проверка формата телефона
        phone_clean = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if not phone_clean.isdigit() or len(phone_clean) < 10:
            return {"valid": False, "error": f"Некорректный формат телефона: {phone}"}

        # Проверка email если указан
        if email and email.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email.strip()):
                return {"valid": False, "error": f"Некорректный формат email: {email}"}

        return {"valid": True, "error": None}

    async def _check_slot_availability(self, staff_id: int, service_ids: List[int], booking_dt: datetime) -> Dict[str, Any]:
        """
        Проверка доступности временного слота (опциональная проверка)

        Returns:
            {"available": bool, "error": str, "suggestion": str} - результат проверки
        """
        try:
            logger.info(f"YTH_CSA: Проверка доступности слота {booking_dt} для мастера {staff_id}...")

            # Проверяем доступность только для первой услуги (для простоты)
            primary_service_id = service_ids[0]

            # Получаем доступные времена на эту дату
            day_str = booking_dt.strftime('%Y-%m-%d')
            available_times = await self.yclients.get_available_times(
                staff_id=staff_id,
                service_id=primary_service_id,
                day=day_str
            )

            if not available_times.get('data'):
                return {
                    "available": False,
                    "error": f"Нет доступных слотов на {day_str}",
                    "suggestion": "Попробуйте выбрать другую дату"
                }

            # Проверяем есть ли точное время в доступных слотах
            requested_time = booking_dt.strftime('%H:%M')
            available_time_slots = [slot.get('time') for slot in available_times['data']]

            if requested_time not in available_time_slots:
                logger.warning(f"YTH_CSA: Время {requested_time} недоступно. Доступные: {available_time_slots[:5]}")
                return {
                    "available": False,
                    "error": f"Время {requested_time} недоступно",
                    "suggestion": f"Доступные времена: {', '.join(available_time_slots[:5])}"
                }

            logger.info(f"YTH_CSA: ✅ Слот {requested_time} доступен")
            return {"available": True, "error": None, "suggestion": None}

        except Exception as e:
            logger.warning(f"YTH_CSA: Ошибка проверки доступности слота: {e}")
            # Не блокируем создание записи из-за ошибки проверки доступности
            return {
                "available": True,  # Разрешаем создание записи
                "error": None,
                "suggestion": f"Не удалось проверить доступность (создание записи разрешено): {str(e)}"
            }

    def _create_enhanced_comment(self, original_comment: str, service_ids: List[int], booking_dt: datetime) -> str:
        """
        Создание расширенного комментария с полезной информацией

        Returns:
            Расширенный комментарий для записи
        """
        enhanced_parts = []

        # Добавляем оригинальный комментарий если есть
        if original_comment and original_comment.strip():
            enhanced_parts.append(f"Комментарий: {original_comment.strip()}")

        # Добавляем техническую информацию
        enhanced_parts.append(f"Услуги ID: {service_ids}")
        enhanced_parts.append(f"Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Добавляем информацию о времени записи
        weekday = booking_dt.strftime('%A')
        time_slot = booking_dt.strftime('%H:%M')
        enhanced_parts.append(f"День недели: {weekday}, время: {time_slot}")

        return " | ".join(enhanced_parts)

    async def handle_create_booking(self, phone: str, fullname: str, service_ids: List[int],
                                  staff_id: int, booking_datetime: str, email: Optional[str] = None,
                                  comment: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Tool handler: создать запись в локальной базе данных с полной валидацией"""
        logger.info(f"YTH_HCB: ═══════════════════════════════════════════════════════════")
        logger.info(f"YTH_HCB: 🎯 СОЗДАНИЕ ЗАПИСИ - НАЧАЛО")
        logger.info(f"YTH_HCB: ═══════════════════════════════════════════════════════════")
        logger.info(f"YTH_HCB: 📋 Входные параметры:")
        logger.info(f"YTH_HCB:    Клиент: '{fullname}' ({phone})")
        logger.info(f"YTH_HCB:    Услуги: {service_ids} (тип: {type(service_ids)})")
        logger.info(f"YTH_HCB:    Мастер: {staff_id} (тип: {type(staff_id)})")
        logger.info(f"YTH_HCB:    Дата: '{booking_datetime}'")
        logger.info(f"YTH_HCB:    Email: '{email}'")
        logger.info(f"YTH_HCB:    Комментарий: '{comment}'")
        logger.info(f"YTH_HCB: ═══════════════════════════════════════════════════════════")

        try:
            # ============================================================================
            # 1. ВАЛИДАЦИЯ ВХОДНЫХ ДАННЫХ
            # ============================================================================

            logger.info("YTH_HCB: 🔍 Этап 1: Валидация входных данных...")

            # Валидация контактной информации
            contact_validation = self._validate_contact_info(phone, fullname, email)
            if not contact_validation["valid"]:
                logger.error(f"YTH_HCB: ❌ Ошибка валидации контактов: {contact_validation['error']}")
                return {"error": f"Некорректные контактные данные: {contact_validation['error']}", "success": False}
            logger.info("YTH_HCB: ✅ Контактные данные валидны")

            # Валидация service_ids
            service_validation = self._validate_service_ids(service_ids)
            if not service_validation["valid"]:
                logger.error(f"YTH_HCB: ❌ Ошибка валидации service_ids: {service_validation['error']}")
                return {"error": f"Некорректные ID услуг: {service_validation['error']}", "success": False}
            logger.info(f"YTH_HCB: ✅ service_ids валидны: {service_ids}")

            # Валидация staff_id
            staff_validation = self._validate_staff_id(staff_id)
            if not staff_validation["valid"]:
                logger.error(f"YTH_HCB: ❌ Ошибка валидации staff_id: {staff_validation['error']}")
                return {"error": f"Некорректный ID мастера: {staff_validation['error']}", "success": False}
            logger.info(f"YTH_HCB: ✅ staff_id валиден: {staff_id}")

            # Валидация даты
            datetime_validation = self._validate_booking_datetime(booking_datetime)
            if not datetime_validation["valid"]:
                logger.error(f"YTH_HCB: ❌ Ошибка валидации даты: {datetime_validation['error']}")
                return {"error": f"Некорректная дата записи: {datetime_validation['error']}", "success": False}
            booking_dt = datetime_validation["parsed_datetime"]
            logger.info(f"YTH_HCB: ✅ Дата валидна: {booking_dt}")

            # ============================================================================
            # 2. ПРОВЕРКА СУЩЕСТВОВАНИЯ УСЛУГ И МАСТЕРА В API
            # ============================================================================

            logger.info("YTH_HCB: 🌐 Этап 2: Проверка существования услуг и мастера в API...")

            # Получаем и проверяем услуги
            try:
                services_data = await self._get_services_from_api()
                if not services_data:
                    logger.error("YTH_HCB: ❌ API вернул пустой список услуг")
                    return {"error": "Не удалось получить список услуг из системы", "success": False}

                logger.info(f"YTH_HCB: 📋 Получено {len(services_data)} услуг из API")

                # Проверяем что все запрашиваемые услуги существуют
                available_service_ids = {s.get('id') for s in services_data if s.get('id')}
                missing_services = [sid for sid in service_ids if sid not in available_service_ids]

                if missing_services:
                    logger.error(f"YTH_HCB: ❌ Услуги не найдены в системе: {missing_services}")
                    logger.error(f"YTH_HCB: 📋 Доступные ID услуг (первые 10): {list(available_service_ids)[:10]}")
                    return {
                        "error": f"Услуги с ID {missing_services} не найдены в системе",
                        "success": False,
                        "available_services": list(available_service_ids)[:20]  # Для отладки
                    }

                logger.info(f"YTH_HCB: ✅ Все услуги найдены в системе: {service_ids}")

            except Exception as e:
                logger.error(f"YTH_HCB: ❌ Ошибка получения услуг из API: {e}")
                return {"error": f"Ошибка связи с системой услуг: {str(e)}", "success": False}

            # Получаем и проверяем мастеров
            try:
                if not self.yclients:
                    logger.error("YTH_HCB: ❌ YClients клиент недоступен")
                    return {"error": "Система недоступна", "success": False}

                staff_list = await self.yclients.get_staff(force_refresh=True, use_real_api=True)
                available_staff_ids = {staff.id if hasattr(staff, 'id') else staff.get('id') for staff in staff_list}

                if staff_id not in available_staff_ids:
                    logger.error(f"YTH_HCB: ❌ Мастер с ID {staff_id} не найден")
                    logger.error(f"YTH_HCB: 👥 Доступные мастера: {list(available_staff_ids)}")
                    return {
                        "error": f"Мастер с ID {staff_id} не найден в системе",
                        "success": False,
                        "available_staff": list(available_staff_ids)  # Для отладки
                    }

                logger.info(f"YTH_HCB: ✅ Мастер найден в системе: {staff_id}")

            except Exception as e:
                logger.error(f"YTH_HCB: ❌ Ошибка получения мастеров из API: {e}")
                return {"error": f"Ошибка связи с системой мастеров: {str(e)}", "success": False}

            # ============================================================================
            # 2.5. ОПЦИОНАЛЬНАЯ ПРОВЕРКА ДОСТУПНОСТИ СЛОТА
            # ============================================================================

            logger.info("YTH_HCB: ⏰ Этап 2.5: Проверка доступности временного слота...")

            slot_check = await self._check_slot_availability(staff_id, service_ids, booking_dt)
            if not slot_check["available"]:
                logger.warning(f"YTH_HCB: ⚠️ Слот может быть недоступен: {slot_check['error']}")
                # Не блокируем создание записи, но предупреждаем
                return {
                    "error": slot_check["error"],
                    "success": False,
                    "suggestion": slot_check["suggestion"],
                    "warning": "Выбранное время может быть недоступно"
                }
            elif slot_check["suggestion"]:
                logger.info(f"YTH_HCB: ℹ️ Информация о слоте: {slot_check['suggestion']}")

            # ============================================================================
            # 3. СОХРАНЕНИЕ В БАЗУ ДАННЫХ
            # ============================================================================

            logger.info("YTH_HCB: 💾 Этап 3: Сохранение в базу данных...")

            with SessionLocal() as db:
                # ============================================================================
                # 3.1 УПРАВЛЕНИЕ КЛИЕНТАМИ
                # ============================================================================

                logger.info("YTH_HCB: 👤 Этап 3.1: Поиск/создание клиента...")
                client = None

                # Сначала пытаемся найти клиента по telegram_id
                if self.telegram_id:
                    client = db.query(Client).filter(Client.telegram_id == str(self.telegram_id)).first()
                    if client:
                        logger.info(f"YTH_HCB: ✅ Найден клиент по Telegram ID: {client.id}")

                # Если не нашли по telegram_id, ищем по телефону
                if not client and phone:
                    normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
                    client = db.query(Client).filter(Client.phone.contains(normalized_phone[-10:])).first()
                    if client:
                        logger.info(f"YTH_HCB: ✅ Найден клиент по телефону: {client.id}")

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
                    logger.info(f"YTH_HCB: ✅ Создан новый клиент ID: {client.id} для {fullname} ({phone})")
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
                        logger.info("YTH_HCB: ✅ Данные клиента обновлены")

                # ============================================================================
                # 3.2 ПОЛУЧЕНИЕ ЧИТАЕМЫХ НАЗВАНИЙ
                # ============================================================================

                logger.info("YTH_HCB: 🏷️ Этап 3.2: Получение читаемых названий...")

                # Получаем названия услуг (уже получили services_data выше)
                services_dict = {s.get('id'): s.get('title', f'Услуга #{s.get("id")}') for s in services_data}
                service_names = []

                for service_id in service_ids:
                    service_name = services_dict.get(service_id, f"Услуга #{service_id}")
                    service_names.append(service_name)
                    logger.info(f"YTH_HCB:    Услуга ID {service_id} -> '{service_name}'")

                # Получаем имя мастера (уже получили staff_list выше)
                staff_name = f"Мастер #{staff_id}"
                for staff in staff_list:
                    staff_id_check = staff.id if hasattr(staff, 'id') else staff.get('id')
                    if staff_id_check == staff_id:
                        staff_name = staff.name if hasattr(staff, 'name') else staff.get('name', f"Мастер #{staff_id}")
                        logger.info(f"YTH_HCB:    Мастер ID {staff_id} -> '{staff_name}'")
                        break

                # ============================================================================
                # 3.3 СОЗДАНИЕ ЗАПИСИ
                # ============================================================================

                logger.info("YTH_HCB: 📝 Этап 3.3: Создание записи в БД...")

                if not client or not client.id:
                    raise ValueError("Не удалось создать или найти клиента")

                # Создаем расширенный комментарий
                enhanced_comment = self._create_enhanced_comment(comment, service_ids, booking_dt)

                appointment = Appointment(
                    client_id=client.id,
                    service_ids=json.dumps(service_ids),  # Сохраняем ID услуг как JSON
                    staff_id=staff_id,  # Сохраняем ID мастера
                    service_name=", ".join(service_names),
                    master_name=staff_name,
                    appointment_datetime=booking_dt,
                    duration_minutes=60,  # TODO: Вычислять из длительности услуг
                    status="scheduled"
                )
                db.add(appointment)
                db.commit()
                db.refresh(appointment)

                # ============================================================================
                # 4. ФОРМИРОВАНИЕ УСПЕШНОГО ОТВЕТА
                # ============================================================================

                logger.info("YTH_HCB: ✅ Этап 4: Формирование ответа...")

                result = {
                    "success": True,
                    "record_id": appointment.id,
                    "client_name": fullname,
                    "phone": phone,
                    "email": email,
                    "services": service_names,
                    "service_ids": service_ids,  # Для внутреннего использования
                    "master": staff_name,
                    "staff_id": staff_id,  # Для внутреннего использования
                    "datetime": booking_dt.isoformat(),
                    "status": "scheduled",
                    "message": "Запись успешно создана в системе",
                    "comment": comment
                }

                logger.info(f"YTH_HCB: ═══════════════════════════════════════════════════════════")
                logger.info(f"YTH_HCB: 🎉 СОЗДАНИЕ ЗАПИСИ - УСПЕХ!")
                logger.info(f"YTH_HCB:    ID записи: {appointment.id}")
                logger.info(f"YTH_HCB:    Клиент: {fullname} (ID: {client.id})")
                logger.info(f"YTH_HCB:    Услуги: {service_names}")
                logger.info(f"YTH_HCB:    Мастер: {staff_name}")
                logger.info(f"YTH_HCB:    Дата: {booking_dt}")
                logger.info(f"YTH_HCB: ═══════════════════════════════════════════════════════════")

                return {"booking": result, "success": True}

        except Exception as e:
            logger.error(f"YTH_HCB: ═══════════════════════════════════════════════════════════")
            logger.error(f"YTH_HCB: ❌ СОЗДАНИЕ ЗАПИСИ - ОШИБКА!")
            logger.error(f"YTH_HCB:    Тип ошибки: {type(e).__name__}")
            logger.error(f"YTH_HCB:    Сообщение: {str(e)}")
            logger.error(f"YTH_HCB: ═══════════════════════════════════════════════════════════")
            import traceback
            logger.error(f"YTH_HCB: Полный стек ошибки:\n{traceback.format_exc()}")
            return {"error": f"Внутренняя ошибка при создании записи: {str(e)}", "success": False}

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
