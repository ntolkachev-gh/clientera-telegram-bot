# YclientsClient - Документация по использованию

## Описание

Модуль `YclientsClient` предоставляет интерфейс для взаимодействия с CRM Yclients. Все методы возвращают мокированные данные для тестирования и разработки.

## Инициализация

```python
from core.yclients_client import YclientsClient
from config import settings

yclients = YclientsClient(
    api_key=settings.youclients_api_key,
    company_id=settings.youclients_company_id
)
```

## Основные возможности

### 1. Получение справочников (с кэшированием)

#### Получение услуг
```python
services = await yclients.get_services()
# Принудительное обновление кэша
services = await yclients.get_services(force_refresh=True)

for service in services:
    print(f"{service.title} - {service.price} руб ({service.duration} мин)")
```

#### Получение мастеров
```python
staff_list = await yclients.get_staff()

for staff in staff_list:
    print(f"{staff.name} - {staff.specialization}")
```

### 2. Поиск свободного времени

```python
from datetime import datetime, timedelta

tomorrow = datetime.now() + timedelta(days=1)
day_after = tomorrow + timedelta(days=1)

# Поиск слотов для конкретных услуг
slots = await yclients.get_available_slots(
    service_ids=[1, 2],  # ID услуг
    date_from=tomorrow,
    date_to=day_after,
    staff_id=1,  # опционально - конкретный мастер
    timezone="Europe/Moscow"
)

for slot in slots:
    print(f"{slot.start.strftime('%Y-%m-%d %H:%M')} - мастер {slot.staff_id}")
```

### 3. Управление записями

#### Создание записи
```python
booking_result = await yclients.create_booking(
    phone="+7999123456",
    fullname="Иван Иванов",
    email="ivan@example.com",  # опционально
    service_ids=[1, 6],  # список ID услуг
    staff_id=2,
    booking_datetime=datetime(2024, 1, 20, 14, 0),
    comment="Первый раз у вас"  # опционально
)

record_id = booking_result["record_id"]
```

#### Отмена записи
```python
cancel_result = await yclients.cancel_booking(
    record_id=record_id,
    reason="Клиент заболел"  # опционально
)
```

### 4. Дополнительные методы

#### Получение записи по ID
```python
booking = await yclients.get_booking_by_id(record_id)
if booking:
    print(f"Клиент: {booking['client_name']}")
    print(f"Статус: {booking['status']}")
```

#### Статистика продаж
```python
from datetime import datetime, timedelta

week_ago = datetime.now() - timedelta(days=7)
stats = await yclients.get_sales_statistics(week_ago, datetime.now())

print(f"Записей: {stats['total_bookings']}")
print(f"Выручка: {stats['total_revenue']} руб")
```

#### Список клиентов
```python
clients = await yclients.get_clients(limit=50, offset=0)
for client in clients:
    print(f"{client['name']} - {client['visits_count']} визитов")
```

### 5. Утилитарные методы

#### Поиск услуги по названию
```python
service = await yclients.find_service_by_name("стрижка")
if service:
    print(f"Найдена: {service.title}")
```

#### Поиск мастера по имени
```python
staff = await yclients.find_staff_by_name("Анна")
if staff:
    print(f"Найден: {staff.name}")
```

### 6. Управление кэшем

```python
# Очистка кэша справочников
yclients.clear_cache()

# Проверка актуальности кэша
is_valid = yclients._is_cache_valid()
```

## Модели данных

### Service
```python
@dataclass
class Service:
    id: int
    title: str
    duration: int  # в минутах
    price: float
    staff_ids: List[int]  # мастера, которые могут выполнить
```

### Staff
```python
@dataclass
class Staff:
    id: int
    name: str
    specialization: Optional[str]
    service_ids: Optional[List[int]]  # услуги, которые может выполнить
```

### TimeSlot
```python
@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    staff_id: int
    available: bool = True
```

### Booking
```python
@dataclass
class Booking:
    record_id: Optional[int]
    client_phone: str
    client_name: str
    client_email: Optional[str]
    service_ids: List[int]
    staff_id: int
    datetime: Optional[datetime]
    comment: Optional[str]
    status: str = "active"
```

## Кэширование

Справочники (услуги и мастера) кэшируются на 1 час для повышения производительности. Кэш автоматически обновляется при истечении времени или может быть принудительно очищен.

## Логирование

Все операции логируются с подробной информацией:
- 🏢 Инициализация клиента
- 📋 Загрузка справочников
- 🔍 Поиск слотов и записей
- 📝 Создание записей
- ❌ Отмена записей
- ✅ Успешные операции

## Запуск тестов

```bash
python test_yclients_client.py
```

Тест демонстрирует все основные возможности модуля с мокированными данными.
