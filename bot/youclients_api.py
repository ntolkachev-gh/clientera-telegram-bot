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
        """Выполнение HTTP запроса к API Youclients"""
        url = f"{self.base_url}/{endpoint}"
        
        logger.info(f"Youclients API {method} запрос: {url}")
        if data:
            logger.info(f"Данные запроса: {data}")
        
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
        """Создание записи клиента"""
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
        
        response = await self._make_request("POST", f"company/{self.company_id}/records", data)
        
        if "error" in response:
            return {"success": False, "error": response["error"]}
        
        return {"success": True, "data": response.get("data", {})}

    async def get_appointments(self, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """Получение списка записей за период"""
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

    async def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """Отмена записи"""
        response = await self._make_request(
            "DELETE", 
            f"company/{self.company_id}/records/{appointment_id}"
        )
        
        if "error" in response:
            return {"success": False, "error": response["error"]}
        
        return {"success": True}

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
        
        formatted = "📋 Доступные услуги:\n\n"
        for service in services:
            price = service.get("price", 0)
            duration = service.get("duration", 0)
            formatted += f"• {service.get('title', 'Без названия')}\n"
            formatted += f"  💰 {price} руб. | ⏱ {duration} мин.\n\n"
        
        return formatted

    async def format_masters_list(self) -> str:
        """Форматирование списка мастеров для отображения пользователю"""
        masters = await self.get_masters()
        
        if not masters:
            return "Мастера не найдены"
        
        formatted = "👩‍💼 Наши мастера:\n\n"
        for master in masters:
            name = f"{master.get('name', '')} {master.get('surname', '')}"
            specialization = master.get('specialization', 'Универсальный мастер')
            formatted += f"• {name}\n"
            formatted += f"  🎯 {specialization}\n\n"
        
        return formatted 