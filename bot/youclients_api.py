import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)


class YouclientsAPI:
    def __init__(self):
        self.base_url = "https://api.youclients.ru/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.youclients_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.company_id = settings.youclients_company_id

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Выполнение HTTP запроса к API Youclients (ВРЕМЕННО ЗАКОММЕНТИРОВАНО)"""
        url = f"{self.base_url}/{endpoint}"

        logger.info(f" Youclients API {method} запрос (ЗАКОММЕНТИРОВАНО): {url}")
        if data:
            logger.info(f" Данные запроса: {data}")

        # ВРЕМЕННО: Возвращаем заглушку вместо реального запроса
        logger.warning(" ВНИМАНИЕ: Реальные запросы к Youclients API временно отключены!")
        logger.info("📝 Запрос будет залогирован, но не отправлен в Youclients")

        # Возвращаем заглушку в зависимости от типа запроса
        if method == "GET" and "services" in endpoint:
            return {
                "data": [
                    {"id": 1, "title": "Стрижка", "price": 1500, "duration": 60},
                    {"id": 2, "title": "Окрашивание", "price": 3000, "duration": 120},
                    {"id": 3, "title": "Укладка", "price": 2000, "duration": 90}
                ]
            }
        elif method == "GET" and "staff" in endpoint:
            return {
                "data": [
                    {"id": 1, "name": "Анна", "surname": "Петрова", "specialization": "Парикмахер"},
                    {"id": 2, "name": "Мария", "surname": "Иванова", "specialization": "Стилист"}
                ]
            }
        elif method == "POST" and "records" in endpoint:
            logger.info(" Запись клиента залогирована (локально)")
            return {"success": True, "data": {"id": 999, "status": "created"}}
        else:
            return {"data": [], "success": True}

        # ЗАКОММЕНТИРОВАННЫЙ КОД - раскомментировать после настройки API
        """
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=self.headers)

                logger.info(f"Youclients API ответ: {response.status_code}")
                logger.info(f"Заголовки ответа: {response.headers}")

                response.raise_for_status()
                response_data = response.json()
                logger.info(f"Данные ответа: {response_data}")
                return response_data

            except httpx.HTTPError as e:
                logger.error(f"Ошибка HTTP запроса к Youclients: {e}")
                logger.error(f"Статус код: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
                logger.error(f"Текст ответа: {e.response.text if hasattr(e, 'response') else 'N/A'}")
                return {"error": str(e)}
            except Exception as e:
                logger.error(f"Неожиданная ошибка при запросе к Youclients: {e}")
                return {"error": str(e)}
        """

    async def get_services(self) -> List[Dict[str, Any]]:
        """Получение списка услуг"""
        response = await self._make_request("GET", f"company/{self.company_id}/services")

        if "error" in response:
            return []

        return response.get("data", [])

    async def get_masters(self) -> List[Dict[str, Any]]:
        """Получение списка мастеров"""
        response = await self._make_request("GET", f"company/{self.company_id}/staff")

        if "error" in response:
            return []

        return response.get("data", [])

    async def get_master_schedule(self, master_id: int, date: str) -> Dict[str, Any]:
        """Получение расписания мастера на определенную дату"""
        response = await self._make_request(
            "GET",
            f"company/{self.company_id}/staff/{master_id}/schedule/{date}"
        )

        if "error" in response:
            return {}

        return response.get("data", {})

    async def get_available_slots(self, service_id: int, master_id: int,
                                date: str, duration: int = 60) -> List[Dict[str, Any]]:
        """Получение доступных временных слотов для записи"""
        params = {
            "service_id": service_id,
            "staff_id": master_id,
            "date": date,
            "duration": duration
        }

        response = await self._make_request(
            "GET",
            f"company/{self.company_id}/book_times",
            params
        )

        if "error" in response:
            return []

        return response.get("data", [])

    async def create_appointment(self, client_data: Dict[str, Any],
                               service_id: int, master_id: int,
                               appointment_datetime: datetime) -> Dict[str, Any]:
        """Создание записи клиента (с сохранением в локальную БД)"""

        # Получаем информацию об услуге и мастере
        services = await self.get_services()
        masters = await self.get_masters()

        service_name = "Неизвестная услуга"
        master_name = "Неизвестный мастер"

        # Находим название услуги
        for service in services:
            if service.get("id") == service_id:
                service_name = service.get("title", "Неизвестная услуга")
                break

        # Находим имя мастера
        for master in masters:
            if master.get("id") == master_id:
                master_name = f"{master.get('name', '')} {master.get('surname', '')}".strip()
                break

        # Данные для отправки в Youclients (залогированы, но не отправлены)
        data = {
            "company_id": self.company_id,
            "staff_id": master_id,
            "services": [
                {
                    "id": service_id,
                    "amount": 1
                }
            ],
            "datetime": appointment_datetime.isoformat(),
            "client": {
                "name": client_data.get("name", ""),
                "phone": client_data.get("phone", ""),
                "email": client_data.get("email", "")
            },
            "comment": client_data.get("comment", "")
        }

        logger.info(f"Создание записи клиента:")
        logger.info(f"    Клиент: {client_data.get('name', 'N/A')}")
        logger.info(f"    Телефон: {client_data.get('phone', 'N/A')}")
        logger.info(f"    Услуга: {service_name}")
        logger.info(f"    Мастер: {master_name}")
        logger.info(f"    Дата/время: {appointment_datetime}")
        logger.info(f"    Комментарий: {client_data.get('comment', 'N/A')}")

        # Сохраняем в локальную базу данных
        try:
            from database.database import get_db
            from database.models import Appointment, Client
            from sqlalchemy.orm import Session as DBSession

            db = next(get_db())

            # Находим или создаем клиента
            client = db.query(Client).filter(
                Client.telegram_id == str(client_data.get("telegram_id"))
            ).first()

            if client:
                # Создаем запись в локальной БД
                appointment = Appointment(
                    client_id=client.id,
                    service_name=service_name,
                    master_name=master_name,
                    appointment_datetime=appointment_datetime,
                    duration_minutes=60,  # По умолчанию
                    status="scheduled"
                )

                db.add(appointment)
                db.commit()
                db.refresh(appointment)

                logger.info(f" Запись сохранена в локальную БД с ID: {appointment.id}")

            else:
                logger.warning(f" Клиент с telegram_id {client_data.get('telegram_id')} не найден в БД")

        except Exception as e:
            logger.error(f" Ошибка сохранения в локальную БД: {e}")

        # ВРЕМЕННО: Возвращаем заглушку вместо реального запроса к Youclients
        logger.warning(" Запрос к Youclients API временно отключен!")
        logger.info("Запись залогирована и сохранена локально")

        return {"success": True, "data": {"id": "local_999", "status": "created_locally"}}

        # ЗАКОММЕНТИРОВАННЫЙ КОД - раскомментировать после настройки API
        """
        response = await self._make_request("POST", f"company/{self.company_id}/records", data)

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True, "data": response.get("data", {})}
        """

    async def get_appointments(self, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """Получение списка записей за период (из локальной БД)"""

        logger.info(f" Получение записей за период: {date_from} - {date_to}")

        try:
            from database.database import get_db
            from database.models import Appointment
            from datetime import datetime

            db = next(get_db())

            # Конвертируем строки в datetime
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d")

            # Получаем записи из локальной БД
            appointments = db.query(Appointment).filter(
                Appointment.appointment_datetime >= start_date,
                Appointment.appointment_datetime <= end_date
            ).all()

            # Конвертируем в формат, совместимый с Youclients API
            result = []
            for appointment in appointments:
                result.append({
                    "id": appointment.id,
                    "datetime": appointment.appointment_datetime.isoformat(),
                    "service_name": appointment.service_name,
                    "master_name": appointment.master_name,
                    "status": appointment.status,
                    "created_at": appointment.created_at.isoformat()
                })

            logger.info(f" Найдено записей в локальной БД: {len(result)}")
            return result

        except Exception as e:
            logger.error(f" Ошибка получения записей из локальной БД: {e}")
            return []

        # ЗАКОММЕНТИРОВАННЫЙ КОД - раскомментировать после настройки API
        """
        params = {
            "date_from": date_from,
            "date_to": date_to
        }

        response = await self._make_request(
            "GET",
            f"company/{self.company_id}/records",
            params
        )

        if "error" in response:
            return []

        return response.get("data", [])
        """

    async def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """Отмена записи (в локальной БД)"""

        logger.info(f" Отмена записи с ID: {appointment_id}")

        try:
            from database.database import get_db
            from database.models import Appointment

            db = next(get_db())

            # Находим запись в локальной БД
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

            if appointment:
                # Обновляем статус
                appointment.status = str("cancelled")
                appointment.updated_at = datetime.utcnow()
                db.commit()

                logger.info(f" Запись {appointment_id} отменена в локальной БД")
                return {"success": True}
            else:
                logger.warning(f" Запись с ID {appointment_id} не найдена в локальной БД")
                return {"success": False, "error": "Запись не найдена"}

        except Exception as e:
            logger.error(f" Ошибка отмены записи в локальной БД: {e}")
            return {"success": False, "error": str(e)}

        # ЗАКОММЕНТИРОВАННЫЙ КОД - раскомментировать после настройки API
        """
        response = await self._make_request(
            "DELETE",
            f"company/{self.company_id}/records/{appointment_id}"
        )

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True}
        """

    async def find_service_by_name(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Поиск услуги по названию"""
        services = await self.get_services()

        for service in services:
            if service_name.lower() in service.get("title", "").lower():
                return service

        return None

    async def find_master_by_name(self, master_name: str) -> Optional[Dict[str, Any]]:
        """Поиск мастера по имени"""
        masters = await self.get_masters()

        for master in masters:
            full_name = f"{master.get('name', '')} {master.get('surname', '')}"
            if master_name.lower() in full_name.lower():
                return master

        return None

    async def get_next_available_slots(self, service_id: int, master_id: int,
                                     days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Получение ближайших доступных слотов на несколько дней вперед"""
        available_slots = []

        for i in range(days_ahead):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            slots = await self.get_available_slots(service_id, master_id, date)

            for slot in slots:
                slot["date"] = date
                available_slots.append(slot)

        return available_slots

    async def format_services_list(self) -> str:
        """Форматирование списка услуг для отображения пользователю"""
        services = await self.get_services()

        if not services:
            return "Услуги не найдены"

        formatted = " Доступные услуги:\n\n"
        for service in services:
            price = service.get("price", 0)
            duration = service.get("duration", 0)
            formatted += f"• {service.get('title', 'Без названия')}\n"
            formatted += f"   {price} руб. |  {duration} мин.\n\n"

        return formatted

    async def format_masters_list(self) -> str:
        """Форматирование списка мастеров для отображения пользователю"""
        masters = await self.get_masters()

        if not masters:
            return "Мастера не найдены"

        formatted = " Наши мастера:\n\n"
        for master in masters:
            name = f"{master.get('name', '')} {master.get('surname', '')}"
            specialization = master.get('specialization', 'Универсальный мастер')
            formatted += f"• {name}\n"
            formatted += f"  🎯 {specialization}\n\n"

        return formatted

    async def create_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание новой услуги"""
        data = {
            "title": service_data.get("title", ""),
            "description": service_data.get("description", ""),
            "price": service_data.get("price", 0),
            "duration": service_data.get("duration", 60),
            "category_id": service_data.get("category_id", None),
            "is_active": service_data.get("is_active", True)
        }

        response = await self._make_request("POST", f"company/{self.company_id}/services", data)

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True, "data": response.get("data", {})}

    async def create_master(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание нового мастера"""
        data = {
            "name": master_data.get("name", ""),
            "surname": master_data.get("surname", ""),
            "phone": master_data.get("phone", ""),
            "email": master_data.get("email", ""),
            "specialization": master_data.get("specialization", ""),
            "is_active": master_data.get("is_active", True),
            "work_schedule": master_data.get("work_schedule", {})
        }

        response = await self._make_request("POST", f"company/{self.company_id}/staff", data)

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True, "data": response.get("data", {})}

    async def delete_service(self, service_id: int) -> Dict[str, Any]:
        """Удаление услуги"""
        response = await self._make_request("DELETE", f"company/{self.company_id}/services/{service_id}")

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True}

    async def delete_master(self, master_id: int) -> Dict[str, Any]:
        """Удаление мастера"""
        response = await self._make_request("DELETE", f"company/{self.company_id}/staff/{master_id}")

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True}
