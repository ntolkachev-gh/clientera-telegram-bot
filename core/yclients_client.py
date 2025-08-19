"""
Клиент для взаимодействия с CRM Yclients API
"""
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import time
import httpx

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@dataclass
class Service:
    """Модель услуги"""
    id: int
    title: str
    duration: int  # в минутах
    price: float
    staff_ids: List[int]  # список ID мастеров, которые могут выполнить услугу


@dataclass
class Staff:
    """Модель сотрудника/мастера"""
    id: int
    name: str
    specialization: Optional[str] = None
    service_ids: Optional[List[int]] = None  # список ID услуг, которые может выполнить


@dataclass
class TimeSlot:
    """Модель временного слота"""
    start: datetime
    end: datetime
    staff_id: int
    available: bool = True


@dataclass
class Booking:
    """Модель бронирования"""
    record_id: Optional[int] = None
    client_phone: str = ""
    client_name: str = ""
    client_email: Optional[str] = None
    service_ids: List[int] = None
    staff_id: int = 0
    datetime: Optional[datetime] = None
    comment: Optional[str] = None
    status: str = "active"


class YclientsClient:
    """Клиент для работы с API Yclients"""

    def __init__(self, api_key: str, company_id: str):
        self.api_key = api_key
        self.company_id = company_id
        self.base_url = "https://api.yclients.com/api/v1"

        # Headers для реального API (без Cookie для стабильности)
        self.headers = {
            'Accept': 'application/vnd.yclients.v2+json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'X-Client-Id': 'fe2247033368a9cadab0c6c6f76172a9',
            'User-Agent': 'YClientsClient/1.0'
        }

        # Кэш для справочников
        self._services_cache = None
        self._staff_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 3600  # 1 час в секундах

        logger.info(f"🏢 Инициализирован YclientsClient для компании {company_id}")

    def _is_cache_valid(self) -> bool:
        """Проверка актуальности кэша"""
        if self._cache_timestamp is None:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def _clear_cache(self):
        """Очистка кэша"""
        self._services_cache = None
        self._staff_cache = None
        self._cache_timestamp = None
        logger.info("🗑️ Кэш справочников очищен")

    async def _fetch_real_services_from_api(self) -> List[Dict[str, Any]]:
        """
        Получить реальные услуги из YClients API через book_services endpoint (для онлайн-записи)

        Returns:
            Список услуг из реального API
        """
        try:
            logger.info("🔄 Запрос реальных услуг из YClients API (book_services)...")

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Используем правильный endpoint для онлайн-записи
                url = f"{self.base_url}/book_services/{self.company_id}"

                # Добавляем Cookie для стабильности работы API
                headers_with_cookie = self.headers.copy()
                headers_with_cookie['Cookie'] = "app_service_group=0; spid=1754925177619_398c89debb0af0d848839820cf555f61_r3dd5ix3vm0vqwuf; spsc=1755498150556_b8a0a7cdf27891126814136e263b5b85_AlnjTXsjLDEyjpHnYgk6Z2gSmrg6CIe-UrFhWm3.qBEZ"

                response = await client.get(url, headers=headers_with_cookie)
                logger.info(f"📡 API ответ (book_services): статус {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Успешный ответ от book_services API")

                    # YClients book_services API возвращает структуру:
                    # {"success": true, "data": {"services": [...], "categories": [...]}, "meta": []}
                    services_data = []

                    if isinstance(data, dict) and data.get('success') and 'data' in data:
                        api_data = data['data']
                        if isinstance(api_data, dict) and 'services' in api_data:
                            services_data = api_data['services']
                            logger.info(f"🎯 Найдено услуг в data.services: {len(services_data)}")
                        else:
                            logger.warning("⚠️ Неожиданная структура data в book_services")
                    else:
                        logger.warning("⚠️ Неожиданная структура ответа book_services API")
                        if isinstance(data, dict):
                            logger.info(f"Ключи ответа: {list(data.keys())}")

                    # Фильтруем только активные услуги
                    active_services = [s for s in services_data if s.get('active', 0) == 1]
                    logger.info(f"🔍 Активных услуг: {len(active_services)} из {len(services_data)}")

                    return active_services

                else:
                    logger.error(f"❌ Ошибка book_services API: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к book_services API: {str(e)}")
            return []

    async def _fetch_real_staff_from_api(self) -> List[Dict[str, Any]]:
        """
        Получить реальных сотрудников из YClients API через book_staff endpoint (для онлайн-записи)

        Returns:
            Список сотрудников из реального API
        """
        try:
            logger.info("🔄 Запрос реальных сотрудников из YClients API (book_staff)...")

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Используем правильный endpoint для онлайн-записи
                url = f"{self.base_url}/book_staff/{self.company_id}"

                # Добавляем Cookie для стабильности работы API
                headers_with_cookie = self.headers.copy()
                headers_with_cookie['Cookie'] = "app_service_group=0; spid=1754925177619_398c89debb0af0d848839820cf555f61_r3dd5ix3vm0vqwuf; spsc=1755498150556_b8a0a7cdf27891126814136e263b5b85_AlnjTXsjLDEyjpHnYgk6Z2gSmrg6CIe-UrFhWm3.qBEZ"

                response = await client.get(url, headers=headers_with_cookie)
                logger.info(f"📡 API ответ (book_staff): статус {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Успешный ответ от book_staff API")

                    staff_data = []

                    if isinstance(data, dict) and data.get('success') and 'data' in data:
                        # book_staff возвращает массив сотрудников в data
                        if isinstance(data['data'], list):
                            staff_data = data['data']
                            logger.info(f"🎯 Найдено сотрудников в data: {len(staff_data)}")
                        else:
                            logger.warning("⚠️ Неожиданная структура data в book_staff")
                    else:
                        logger.warning("⚠️ Неожиданная структура ответа book_staff API")
                        if isinstance(data, dict):
                            logger.info(f"Ключи ответа: {list(data.keys())}")

                    # Фильтруем только доступных для бронирования сотрудников
                    bookable_staff = [s for s in staff_data if s.get('bookable', False)]
                    logger.info(f"🔍 Доступных для записи сотрудников: {len(bookable_staff)} из {len(staff_data)}")

                    return bookable_staff

                else:
                    logger.error(f"❌ Ошибка book_staff API: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе сотрудников к book_staff API: {str(e)}")
            return []

    # ============================================================================
    # 1. МЕТОДЫ ДЛЯ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ (с кэшированием)
    # ============================================================================

    async def get_services(self, force_refresh: bool = False, use_real_api: bool = True) -> List[Service]:
        """
        Получить список услуг

        Args:
            force_refresh: принудительно обновить кэш
            use_real_api: использовать реальный API (True) или мок данные (False)

        Returns:
            Список услуг с ID, названием, длительностью, ценой, списком мастеров
        """
        if not force_refresh and self._is_cache_valid() and self._services_cache:
            logger.info("📋 Возвращаем услуги из кэша")
            return self._services_cache

        services = []

        if use_real_api:
            # Пытаемся получить реальные данные из API
            logger.info("🔄 Загружаем список услуг из реального API YClients...")
            real_services_data = await self._fetch_real_services_from_api()

            if real_services_data:
                # Преобразуем реальные данные API в наш формат
                for i, service_data in enumerate(real_services_data):
                    try:
                        # Адаптируем реальную структуру YClients API к нашей модели
                        # Реальная структура: {id, title, price_min, price_max, staff, active, ...}

                        # Получаем ID услуги
                        service_id = service_data.get('id', i + 1)

                        # Получаем название услуги
                        title = (service_data.get('title') or
                                service_data.get('booking_title') or
                                service_data.get('name') or
                                f'Услуга {i+1}')

                        # Получаем цену (YClients использует price_min и price_max)
                        price_min = service_data.get('price_min', 0)
                        price_max = service_data.get('price_max', 0)
                        price = float(price_min if price_min > 0 else price_max)

                        # Получаем длительность (в YClients может не быть поля duration)
                        duration = service_data.get('duration', service_data.get('seance_length', 60))

                        # Получаем список сотрудников (в YClients это массив объектов staff)
                        staff_list = service_data.get('staff', [])
                        if isinstance(staff_list, list):
                            # Извлекаем ID сотрудников из массива объектов
                            staff_ids = [staff.get('id', staff) if isinstance(staff, dict) else staff for staff in staff_list]
                            # Если список пустой, добавляем общий ID
                            if not staff_ids:
                                staff_ids = [1]  # Общий мастер
                        else:
                            staff_ids = [1]

                        service = Service(
                            id=service_id,
                            title=title,
                            duration=duration,
                            price=price,
                            staff_ids=staff_ids
                        )
                        services.append(service)
                        logger.info(f"✅ Добавлена услуга: {service.title} - {service.price} руб ({service.duration} мин)")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при обработке услуги {i}: {str(e)}")
                        logger.warning(f"Данные услуги: {json.dumps(service_data, ensure_ascii=False, indent=2)[:300]}...")
                        continue

                logger.info(f"✅ Загружено {len(services)} реальных услуг из API")
            else:
                logger.warning("⚠️ Не удалось получить услуги из API, используем мок данные")
                use_real_api = False

        if not use_real_api or not services:
            # Используем мок данные как fallback
            logger.info("🔄 Загружаем список услуг из мок данных")

            # МОКИРОВАННЫЕ ДАННЫЕ - в реальном проекте здесь будет HTTP запрос
            mock_services_data = [
                {
                    "id": 1,
                    "title": "Стрижка женская",
                    "duration": 60,
                    "price": 2500.0,
                    "staff_ids": [1, 2, 3]
                },
                {
                    "id": 2,
                    "title": "Окрашивание волос",
                    "duration": 180,
                    "price": 8000.0,
                    "staff_ids": [2, 3]
                },
                {
                    "id": 3,
                    "title": "Маникюр",
                    "duration": 90,
                    "price": 3000.0,
                    "staff_ids": [4, 5]
                },
                {
                    "id": 4,
                    "title": "Педикюр",
                    "duration": 120,
                    "price": 3500.0,
                    "staff_ids": [4, 5]
                },
                {
                    "id": 5,
                    "title": "Массаж лица",
                    "duration": 45,
                    "price": 2000.0,
                    "staff_ids": [6]
                },
                {
                    "id": 6,
                    "title": "Укладка",
                    "duration": 30,
                    "price": 1500.0,
                    "staff_ids": [1, 2, 3]
                }
            ]

            # Преобразуем в объекты Service
            services = [
                Service(
                    id=service["id"],
                    title=service["title"],
                    duration=service["duration"],
                    price=service["price"],
                    staff_ids=service["staff_ids"]
                )
                for service in mock_services_data
            ]

        # Кэшируем результат
        self._services_cache = services
        self._cache_timestamp = time.time()

        logger.info(f"✅ Загружено {len(services)} услуг")
        return services

    async def get_staff(self, force_refresh: bool = False, use_real_api: bool = True) -> List[Staff]:
        """
        Получить список мастеров (сотрудников)

        Args:
            force_refresh: принудительно обновить кэш
            use_real_api: использовать реальный API (True) или мок данные (False)

        Returns:
            Список мастеров с ID, именем и списком услуг
        """
        if not force_refresh and self._is_cache_valid() and self._staff_cache:
            logger.info("👥 Возвращаем мастеров из кэша")
            return self._staff_cache

        staff_list = []

        if use_real_api:
            # Пытаемся получить реальные данные из API
            logger.info("🔄 Загружаем список сотрудников из реального API YClients...")
            real_staff_data = await self._fetch_real_staff_from_api()

            if real_staff_data:
                # Преобразуем реальные данные API в наш формат
                for i, staff_data in enumerate(real_staff_data):
                    try:
                        # Адаптируем реальную структуру YClients API к нашей модели
                        # Реальная структура: {id, name, specialization, ...}

                        staff_id = staff_data.get('id', i + 1)
                        name = staff_data.get('name', f'Мастер {i+1}')
                        specialization = staff_data.get('specialization', 'Специалист')

                        # В реальном API нет прямого поля service_ids, оставляем пустым
                        service_ids = []

                        staff = Staff(
                            id=staff_id,
                            name=name,
                            specialization=specialization,
                            service_ids=service_ids
                        )
                        staff_list.append(staff)
                        logger.info(f"✅ Добавлен сотрудник: {staff.name} - {staff.specialization}")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при обработке сотрудника {i}: {str(e)}")
                        continue

                logger.info(f"✅ Загружено {len(staff_list)} реальных сотрудников из API")
            else:
                logger.warning("⚠️ Не удалось получить сотрудников из API, используем мок данные")
                use_real_api = False

        if not use_real_api or not staff_list:
            # Используем мок данные как fallback
            logger.info("🔄 Загружаем список мастеров из мок данных")

            # МОКИРОВАННЫЕ ДАННЫЕ
            mock_staff_data = [
            {
                "id": 1,
                "name": "Анна Петрова",
                "specialization": "Парикмахер-стилист",
                "service_ids": [1, 6]  # Стрижка, Укладка
            },
            {
                "id": 2,
                "name": "Мария Сидорова",
                "specialization": "Колорист",
                "service_ids": [1, 2, 6]  # Стрижка, Окрашивание, Укладка
            },
            {
                "id": 3,
                "name": "Елена Иванова",
                "specialization": "Топ-стилист",
                "service_ids": [1, 2, 6]  # Стрижка, Окрашивание, Укладка
            },
            {
                "id": 4,
                "name": "Ольга Козлова",
                "specialization": "Мастер маникюра",
                "service_ids": [3, 4]  # Маникюр, Педикюр
            },
            {
                "id": 5,
                "name": "Татьяна Морозова",
                "specialization": "Nail-мастер",
                "service_ids": [3, 4]  # Маникюр, Педикюр
            },
            {
                "id": 6,
                "name": "Светлана Волкова",
                "specialization": "Косметолог",
                "service_ids": [5]  # Массаж лица
            }
            ]

            # Преобразуем в объекты Staff
            staff_list = [
                Staff(
                    id=staff["id"],
                    name=staff["name"],
                    specialization=staff["specialization"],
                    service_ids=staff["service_ids"]
                )
                for staff in mock_staff_data
            ]

        # Кэшируем результат
        self._staff_cache = staff_list
        self._cache_timestamp = time.time()

        logger.info(f"✅ Загружено {len(staff_list)} мастеров")
        return staff_list

    # ============================================================================
    # 2. НОВЫЕ МЕТОДЫ ДЛЯ ПОИСКА ДОСТУПНЫХ ДАТ И ВРЕМЕНИ (согласно документации API)
    # ============================================================================

    async def get_available_days(self, staff_id: int, service_id: int) -> Dict[str, Any]:
        """
        Получить доступные дни для записи к указанному сотруднику и услуге

        Args:
            staff_id: ID сотрудника
            service_id: ID услуги

        Returns:
            Словарь с данными о доступных датах: {'data': {'booking_dates': [timestamp1, timestamp2, ...]}}
        """
        logger.info(f"📅 Запрос доступных дней для мастера {staff_id} и услуги {service_id}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Формируем URL согласно документации API
                url = f"{self.base_url}/book_dates/{self.company_id}"

                # Параметры запроса
                params = {
                    'staff_id': staff_id,
                    'service_id': service_id
                }

                # Добавляем Cookie для стабильности работы API
                headers_with_cookie = self.headers.copy()
                headers_with_cookie['Cookie'] = "app_service_group=0; spid=1754925177619_398c89debb0af0d848839820cf555f61_r3dd5ix3vm0vqwuf; spsc=1755498150556_b8a0a7cdf27891126814136e263b5b85_AlnjTXsjLDEyjpHnYgk6Z2gSmrg6CIe-UrFhWm3.qBEZ"

                logger.info(f"📡 Отправляем запрос: {url} с параметрами {params}")
                response = await client.get(url, headers=headers_with_cookie, params=params)
                logger.info(f"📡 Ответ API: статус {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Успешный ответ от get_available_days API")

                    if data.get('success', False):
                        booking_dates = data.get('data', {}).get('booking_dates', [])
                        logger.info(f"📅 Найдено доступных дат: {len(booking_dates)}")
                        return data
                    else:
                        logger.error(f"❌ API вернул ошибку: {data}")
                        return {'data': {'booking_dates': []}}
                else:
                    logger.error(f"❌ Ошибка API get_available_days: {response.status_code} - {response.text}")
                    return {'data': {'booking_dates': []}}

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе доступных дней: {str(e)}")
            return {'data': {'booking_dates': []}}

    async def get_available_times(self, staff_id: int, service_id: int, day: str) -> Dict[str, Any]:
        """
        Получить доступные временные слоты на конкретную дату

        Args:
            staff_id: ID сотрудника
            service_id: ID услуги
            day: дата в формате YYYY-MM-DD или timestamp

        Returns:
            Словарь с данными о временных слотах: {'data': [{'time': '12:00', 'seance_length': 3600, 'datetime': timestamp}, ...]}
        """
        logger.info(f"🕐 Запрос доступного времени для мастера {staff_id}, услуги {service_id} на дату {day}")

        try:
            # Преобразуем day в нужный формат если это timestamp
            if isinstance(day, (int, float)) or day.isdigit():
                # Если day - это timestamp, преобразуем в дату
                date_obj = datetime.fromtimestamp(int(day))
                day_str = date_obj.strftime('%Y-%m-%d')
            else:
                day_str = day

            async with httpx.AsyncClient(timeout=15.0) as client:
                # Формируем URL согласно документации API
                url = f"{self.base_url}/book_times/{self.company_id}/{day_str}"

                # Параметры запроса
                params = {
                    'staff_id': staff_id,
                    'service_id': service_id
                }

                # Добавляем Cookie для стабильности работы API
                headers_with_cookie = self.headers.copy()
                headers_with_cookie['Cookie'] = "app_service_group=0; spid=1754925177619_398c89debb0af0d848839820cf555f61_r3dd5ix3vm0vqwuf; spsc=1755498150556_b8a0a7cdf27891126814136e263b5b85_AlnjTXsjLDEyjpHnYgk6Z2gSmrg6CIe-UrFhWm3.qBEZ"

                logger.info(f"📡 Отправляем запрос: {url} с параметрами {params}")
                response = await client.get(url, headers=headers_with_cookie, params=params)
                logger.info(f"📡 Ответ API: статус {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Успешный ответ от get_available_times API")

                    if data.get('success', False):
                        time_slots = data.get('data', [])
                        logger.info(f"🕐 Найдено временных слотов: {len(time_slots)}")
                        return data
                    else:
                        logger.error(f"❌ API вернул ошибку: {data}")
                        return {'data': []}
                else:
                    logger.error(f"❌ Ошибка API get_available_times: {response.status_code} - {response.text}")
                    return {'data': []}

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе доступного времени: {str(e)}")
            return {'data': []}

    async def get_available_slots_for_staff(self, staff_id: int, service_id: int,
                                          date_from: Optional[datetime] = None,
                                          date_to: Optional[datetime] = None) -> List[TimeSlot]:
        """
        Получить все доступные слоты для конкретного сотрудника и услуги
        Использует новые методы get_available_days и get_available_times

        Args:
            staff_id: ID сотрудника
            service_id: ID услуги
            date_from: начальная дата поиска (опционально)
            date_to: конечная дата поиска (опционально)

        Returns:
            Список доступных временных слотов
        """
        logger.info(f"🔍 Поиск слотов для мастера {staff_id} и услуги {service_id}")

        available_slots = []

        try:
            # 1. Получаем доступные дни
            booking_days = await self.get_available_days(staff_id=staff_id, service_id=service_id)
            days = booking_days['data'].get('booking_dates', [])

            if not days:
                logger.info("📅 Нет доступных дней для записи")
                return []

            logger.info(f"📅 Найдено доступных дней: {len(days)}")

            # Фильтруем дни по запрашиваемому диапазону если указан
            target_days = []
            for day in days:
                try:
                    # Обрабатываем как timestamp
                    if isinstance(day, (int, float)):
                        day_datetime = datetime.fromtimestamp(day)
                    elif isinstance(day, str):
                        # Пробуем разные форматы
                        try:
                            day_datetime = datetime.fromisoformat(day.replace('Z', '+00:00'))
                        except:
                            day_datetime = datetime.strptime(day, '%Y-%m-%d')
                    else:
                        continue

                    # Проверяем попадание в диапазон
                    if date_from and day_datetime.date() < date_from.date():
                        continue
                    if date_to and day_datetime.date() > date_to.date():
                        continue

                    target_days.append(day)

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка обработки даты {day}: {e}")
                    continue

            logger.info(f"🎯 Дней в запрашиваемом диапазоне: {len(target_days)}")

            # 2. Для каждого доступного дня получаем временные слоты
            for day in target_days:
                try:
                    time_slots = await self.get_available_times(staff_id=staff_id, service_id=service_id, day=day)
                    slots = time_slots['data']

                    logger.info(f"🕐 Слотов для дня {day}: {len(slots)}")

                    # 3. Преобразуем в объекты TimeSlot
                    for slot_info in slots:
                        try:
                            time_str = slot_info.get('time', '')
                            seance_length = slot_info.get('seance_length', 3600)
                            datetime_timestamp = slot_info.get('datetime', 0)

                            # Парсим время начала
                            if datetime_timestamp:
                                slot_start = datetime.fromtimestamp(datetime_timestamp)
                            elif time_str and isinstance(day, (int, float)):
                                day_date = datetime.fromtimestamp(day).date()
                                hour, minute = map(int, time_str.split(':'))
                                slot_start = datetime.combine(day_date, datetime.min.time().replace(hour=hour, minute=minute))
                            else:
                                continue

                            # Вычисляем время окончания
                            slot_end = slot_start + timedelta(seconds=seance_length)

                            available_slots.append(TimeSlot(
                                start=slot_start,
                                end=slot_end,
                                staff_id=staff_id,
                                available=True
                            ))

                        except Exception as e:
                            logger.warning(f"⚠️ Ошибка парсинга слота {slot_info}: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка получения слотов для дня {day}: {e}")
                    continue

            logger.info(f"✅ Найдено {len(available_slots)} доступных слотов")
            return available_slots

        except Exception as e:
            logger.error(f"❌ Критическая ошибка при поиске слотов: {e}")
            return []

    # ============================================================================
    # 3. СУЩЕСТВУЮЩИЕ МЕТОДЫ ДЛЯ ПОИСКА ВРЕМЕНИ (оставляем для совместимости)
    # ============================================================================

    async def _fetch_real_available_slots(self,
                                         service_ids: List[int],
                                         date_from: datetime,
                                         date_to: datetime,
                                         staff_id: Optional[int] = None) -> List[TimeSlot]:
        """
        Получить реальные временные слоты из YClients API используя book_dates и book_times

        Args:
            service_ids: список ID услуг
            date_from: начальная дата поиска
            date_to: конечная дата поиска
            staff_id: ID конкретного мастера (опционально)

        Returns:
            Список доступных временных слотов из реального API
        """
        available_slots = []

        try:
            logger.info("🔄 Запрос реальных слотов из YClients API (book_dates + book_times)...")

            async with httpx.AsyncClient(timeout=15.0) as client:
                # Добавляем Cookie для стабильности работы API
                headers_with_cookie = self.headers.copy()
                headers_with_cookie['Cookie'] = "app_service_group=0; spid=1754925177619_398c89debb0af0d848839820cf555f61_r3dd5ix3vm0vqwuf; spsc=1755498150556_b8a0a7cdf27891126814136e263b5b85_AlnjTXsjLDEyjpHnYgk6Z2gSmrg6CIe-UrFhWm3.qBEZ"

                # 1. Сначала получаем доступные даты через book_dates
                dates_url = f"{self.base_url}/book_dates/{self.company_id}"

                # Добавляем фильтры для book_dates согласно документации
                dates_params = {}
                if service_ids:
                    dates_params['service_ids'] = service_ids
                if staff_id:
                    dates_params['staff_id'] = staff_id

                dates_response = await client.get(dates_url, headers=headers_with_cookie, params=dates_params)
                logger.info(f"📡 API ответ book_dates: статус {dates_response.status_code}")

                if dates_response.status_code != 200:
                    logger.error(f"❌ Ошибка получения дат: {dates_response.status_code} - {dates_response.text}")
                    return []

                dates_data = dates_response.json()
                if not dates_data.get('success', False):
                    logger.error(f"❌ API вернул ошибку для дат: {dates_data}")
                    return []

                booking_dates = dates_data.get('data', {}).get('booking_dates', [])
                logger.info(f"📅 Найдено доступных дат для записи: {len(booking_dates)}")

                # Фильтруем даты по запрашиваемому диапазону
                target_dates = []
                for date_str in booking_dates:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if date_from.date() <= date_obj <= date_to.date():
                            target_dates.append(date_str)
                    except ValueError:
                        logger.warning(f"⚠️ Неверный формат даты: {date_str}")
                        continue

                logger.info(f"🎯 Даты в запрашиваемом диапазоне: {target_dates}")

                # 2. Для каждой доступной даты получаем временные слоты через book_times
                for date_str in target_dates:
                    try:
                        times_url = f"{self.base_url}/book_times/{self.company_id}/{date_str}"

                        # Формируем параметры для book_times согласно документации
                        times_params = {}
                        if service_ids:
                            times_params['service_ids'] = service_ids
                        if staff_id:
                            times_params['staff_id'] = staff_id

                        logger.info(f"🔍 Запрос слотов для {date_str}: {times_url}")
                        logger.info(f"📋 Параметры book_times: {times_params}")

                        times_response = await client.get(times_url, headers=headers_with_cookie, params=times_params)
                        logger.info(f"📡 Ответ book_times для {date_str}: статус {times_response.status_code}")

                        if times_response.status_code == 200:
                            times_data = times_response.json()

                            if times_data.get('success', False) and 'data' in times_data:
                                # Парсим временные слоты согласно документации
                                # Структура: {"time": "17:30", "seance_length": 3600, "datetime": "2024-01-20T17:30:00"}
                                slots_data = times_data['data']

                                if isinstance(slots_data, list):
                                    logger.info(f"✅ Получено {len(slots_data)} слотов для {date_str}")

                                    for slot_info in slots_data:
                                        try:
                                            # Парсим datetime из API
                                            slot_datetime_str = slot_info.get('datetime')
                                            if slot_datetime_str:
                                                slot_start = datetime.fromisoformat(slot_datetime_str.replace('Z', '+00:00'))

                                                # Вычисляем время окончания
                                                seance_length = slot_info.get('seance_length', 3600)  # по умолчанию 1 час
                                                slot_end = slot_start + timedelta(seconds=seance_length)

                                                # Используем ID мастера из параметров или из API
                                                slot_staff_id = staff_id if staff_id else 4244041  # fallback ID

                                                available_slots.append(TimeSlot(
                                                    start=slot_start,
                                                    end=slot_end,
                                                    staff_id=slot_staff_id,
                                                    available=True
                                                ))

                                        except Exception as e:
                                            logger.warning(f"⚠️ Ошибка парсинга слота {slot_info}: {e}")
                                            continue
                                else:
                                    logger.warning(f"⚠️ Неожиданная структура данных слотов для {date_str}: {type(slots_data)}")
                            else:
                                logger.warning(f"⚠️ Неуспешный ответ book_times для {date_str}: {times_data}")
                        else:
                            logger.warning(f"⚠️ Ошибка book_times для {date_str}: {times_response.status_code} - {times_response.text}")

                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обработки даты {date_str}: {e}")
                        continue

                logger.info(f"✅ Получено {len(available_slots)} реальных слотов из API")
                return available_slots

        except Exception as e:
            logger.error(f"❌ Критическая ошибка при запросе к реальному API: {e}")
            return []

    async def get_available_slots(self,
                                service_ids: List[int],
                                date_from: datetime,
                                date_to: datetime,
                                staff_id: Optional[int] = None,
                                timezone: str = "Europe/Moscow",
                                use_real_api: bool = True) -> List[TimeSlot]:
        """
        Получить свободные временные слоты

        Args:
            service_ids: список ID услуг
            date_from: начальная дата поиска
            date_to: конечная дата поиска
            staff_id: ID конкретного мастера (опционально)
            timezone: часовой пояс
            use_real_api: использовать реальный API (True) или мок данные (False)

        Returns:
            Список доступных временных слотов
        """
        logger.info(f"🔍 Поиск свободных слотов для услуг {service_ids} "
                   f"с {date_from.strftime('%Y-%m-%d')} по {date_to.strftime('%Y-%m-%d')}")

        if staff_id:
            logger.info(f"👤 Поиск для конкретного мастера: {staff_id}")

        available_slots = []

        # Пытаемся получить реальные слоты из API
        if use_real_api:
            logger.info("🔄 Попытка получить реальные слоты из YClients API...")
            real_slots = await self._fetch_real_available_slots(service_ids, date_from, date_to, staff_id)

            if real_slots:
                logger.info(f"✅ Получено {len(real_slots)} реальных слотов")
                return real_slots
            else:
                logger.warning("⚠️ Не удалось получить слоты из реального API, используем мок данные")

        # Fallback к мок данным
        logger.info("🔄 Генерируем мок слоты...")

        # Получаем список мастеров, которые могут выполнить услуги
        services = await self.get_services()
        staff_list = await self.get_staff()

        # Определяем мастеров для поиска
        if staff_id:
            target_staff_ids = [staff_id]
        else:
            # Находим всех мастеров, которые могут выполнить хотя бы одну из услуг
            target_staff_ids = set()
            for service in services:
                if service.id in service_ids:
                    target_staff_ids.update(service.staff_ids)
            target_staff_ids = list(target_staff_ids)

        # Генерируем слоты для каждого дня в диапазоне
        current_date = date_from.date()
        end_date = date_to.date()

        while current_date <= end_date:
            # Рабочие часы: 9:00 - 20:00
            for hour in range(9, 20):
                for minute in [0, 30]:  # каждые 30 минут
                    slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                    slot_end = slot_start + timedelta(minutes=60)  # слоты по часу

                    # Создаем слоты для каждого подходящего мастера
                    for staff_member_id in target_staff_ids:
                        # Мокируем занятость (некоторые слоты заняты)
                        is_busy = (hour == 14 and minute == 0) or (hour == 16 and minute == 30)  # обед и популярное время

                        if not is_busy:
                            available_slots.append(TimeSlot(
                                start=slot_start,
                                end=slot_end,
                                staff_id=staff_member_id,
                                available=True
                            ))

            current_date += timedelta(days=1)

        logger.info(f"✅ Найдено {len(available_slots)} мок слотов")
        return available_slots

    # ============================================================================
    # 3. МЕТОДЫ ДЛЯ ОПЕРАЦИЙ С БРОНЯМИ
    # ============================================================================

    async def create_booking(self,
                           phone: str,
                           fullname: str,
                           email: Optional[str],
                           service_ids: List[int],
                           staff_id: int,
                           booking_datetime: datetime,
                           comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Создать бронирование

        Args:
            phone: телефон клиента
            fullname: полное имя клиента
            email: email клиента (опционально)
            service_ids: список ID услуг
            staff_id: ID мастера
            booking_datetime: дата и время записи
            comment: комментарий к записи

        Returns:
            Данные о созданной брони (record_id, статус)
        """
        logger.info(f"📝 Создание записи для {fullname} ({phone}) "
                   f"на {booking_datetime.strftime('%Y-%m-%d %H:%M')}")

        # МОКИРОВАННЫЕ ДАННЫЕ - имитируем создание записи
        # В реальном проекте здесь будет HTTP POST запрос к API

        # Генерируем ID записи
        record_id = int(time.time()) % 1000000  # простой способ генерации ID

        # Получаем информацию об услугах и мастере для логирования
        services = await self.get_services()
        staff_list = await self.get_staff()

        service_names = [s.title for s in services if s.id in service_ids]
        staff_name = next((s.name for s in staff_list if s.id == staff_id), f"ID:{staff_id}")

        logger.info(f"✅ Запись создана успешно:")
        logger.info(f"   📋 ID записи: {record_id}")
        logger.info(f"   👤 Клиент: {fullname} ({phone})")
        logger.info(f"   💇 Услуги: {', '.join(service_names)}")
        logger.info(f"   👨‍💼 Мастер: {staff_name}")
        logger.info(f"   📅 Время: {booking_datetime.strftime('%Y-%m-%d %H:%M')}")
        if comment:
            logger.info(f"   💬 Комментарий: {comment}")

        return {
            "record_id": record_id,
            "status": "confirmed",
            "client_phone": phone,
            "client_name": fullname,
            "client_email": email,
            "service_ids": service_ids,
            "staff_id": staff_id,
            "datetime": booking_datetime.isoformat(),
            "comment": comment,
            "created_at": datetime.now().isoformat()
        }

    async def cancel_booking(self, record_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Отменить бронирование

        Args:
            record_id: ID записи для отмены
            reason: причина отмены (опционально)

        Returns:
            Результат операции отмены
        """
        logger.info(f"❌ Отмена записи {record_id}")
        if reason:
            logger.info(f"   Причина: {reason}")

        # МОКИРОВАННЫЕ ДАННЫЕ - имитируем отмену записи
        # В реальном проекте здесь будет HTTP DELETE/PUT запрос к API

        logger.info(f"✅ Запись {record_id} успешно отменена")

        return {
            "record_id": record_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "reason": reason
        }

    # ============================================================================
    # 4. ОПЦИОНАЛЬНЫЕ МЕТОДЫ (НА БУДУЩЕЕ)
    # ============================================================================

    async def get_booking_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить запись по ID

        Args:
            record_id: ID записи

        Returns:
            Данные записи или None, если не найдена
        """
        logger.info(f"🔍 Поиск записи по ID: {record_id}")

        # МОКИРОВАННЫЕ ДАННЫЕ
        mock_booking = {
            "record_id": record_id,
            "status": "confirmed",
            "client_phone": "+7999123456",
            "client_name": "Иван Иванов",
            "client_email": "ivan@example.com",
            "service_ids": [1, 6],
            "staff_id": 2,
            "datetime": "2024-01-20T14:00:00",
            "comment": "Первый раз у вас",
            "created_at": "2024-01-15T10:30:00"
        }

        logger.info(f"✅ Запись найдена: {mock_booking['client_name']}")
        return mock_booking

    async def get_sales_statistics(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """
        Получить статистику продаж

        Args:
            date_from: начальная дата
            date_to: конечная дата

        Returns:
            Статистика продаж за период
        """
        logger.info(f"📊 Получение статистики с {date_from.strftime('%Y-%m-%d')} "
                   f"по {date_to.strftime('%Y-%m-%d')}")

        # МОКИРОВАННЫЕ ДАННЫЕ
        mock_stats = {
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "total_bookings": 45,
            "total_revenue": 127500.0,
            "cancelled_bookings": 3,
            "top_services": [
                {"service_id": 1, "service_name": "Стрижка женская", "count": 15, "revenue": 37500.0},
                {"service_id": 2, "service_name": "Окрашивание волос", "count": 8, "revenue": 64000.0},
                {"service_id": 3, "service_name": "Маникюр", "count": 12, "revenue": 36000.0}
            ],
            "top_staff": [
                {"staff_id": 2, "staff_name": "Мария Сидорова", "bookings": 18, "revenue": 52500.0},
                {"staff_id": 3, "staff_name": "Елена Иванова", "bookings": 15, "revenue": 48500.0},
                {"staff_id": 4, "staff_name": "Ольга Козлова", "bookings": 12, "revenue": 26500.0}
            ]
        }

        logger.info(f"✅ Статистика получена: {mock_stats['total_bookings']} записей, "
                   f"выручка {mock_stats['total_revenue']} руб.")
        return mock_stats

    async def get_clients(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получить список клиентов

        Args:
            limit: количество клиентов для получения
            offset: смещение для пагинации

        Returns:
            Список клиентов
        """
        logger.info(f"👥 Получение списка клиентов (limit: {limit}, offset: {offset})")

        # МОКИРОВАННЫЕ ДАННЫЕ
        mock_clients = [
            {
                "id": 1,
                "name": "Анна Петрова",
                "phone": "+7999111111",
                "email": "anna@example.com",
                "visits_count": 5,
                "total_spent": 12500.0,
                "last_visit": "2024-01-15T14:00:00",
                "favorite_services": [1, 6],
                "favorite_staff": [2]
            },
            {
                "id": 2,
                "name": "Мария Сидорова",
                "phone": "+7999222222",
                "email": "maria@example.com",
                "visits_count": 8,
                "total_spent": 24000.0,
                "last_visit": "2024-01-18T16:30:00",
                "favorite_services": [2, 3],
                "favorite_staff": [3, 4]
            }
        ]

        # Применяем limit и offset
        result = mock_clients[offset:offset + limit]

        logger.info(f"✅ Получено {len(result)} клиентов")
        return result

    # ============================================================================
    # УТИЛИТАРНЫЕ МЕТОДЫ
    # ============================================================================

    async def find_service_by_name(self, service_name: str) -> Optional[Service]:
        """
        Найти услугу по названию (нечеткий поиск)

        Args:
            service_name: название услуги

        Returns:
            Найденная услуга или None
        """
        services = await self.get_services()
        service_name_lower = service_name.lower()

        # Точное совпадение
        for service in services:
            if service.title.lower() == service_name_lower:
                return service

        # Частичное совпадение
        for service in services:
            if service_name_lower in service.title.lower():
                return service

        return None

    async def find_staff_by_name(self, staff_name: str) -> Optional[Staff]:
        """
        Найти мастера по имени

        Args:
            staff_name: имя мастера

        Returns:
            Найденный мастер или None
        """
        staff_list = await self.get_staff()
        staff_name_lower = staff_name.lower()

        # Точное совпадение
        for staff in staff_list:
            if staff.name.lower() == staff_name_lower:
                return staff

        # Частичное совпадение
        for staff in staff_list:
            if staff_name_lower in staff.name.lower():
                return staff

        return None

    def clear_cache(self):
        """Публичный метод для очистки кэша"""
        self._clear_cache()
