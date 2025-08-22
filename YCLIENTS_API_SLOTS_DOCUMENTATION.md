# YClients API - Получение доступных слотов для мастера

## Анализ документации и реализация

### 1. Основные методы API для получения слотов

Согласно официальной документации YClients API, для получения доступных слотов используется следующая последовательность запросов:

#### 1.1. Получение списка услуг
```http
GET /api/v1/book_services/{company_id}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "services": [
      {
        "id": 19437973,
        "title": "Наращивание ресниц (объем классический)",
        "price_min": 2190,
        "price_max": 2190,
        "active": 1,
        "category_id": 123,
        "seance_length": 7200  // в секундах
      }
    ],
    "categories": [...]
  }
}
```

#### 1.2. Получение списка мастеров
```http
GET /api/v1/book_staff/{company_id}?service_ids[]={service_id}
```

**Параметры:**
- `service_ids[]` - массив ID услуг (фильтр)
- `datetime` - дата в формате ISO8601 (опционально)

**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "id": 3884784,
      "name": "Джамиля Хункаева",
      "specialization": "Lash-специалист",
      "bookable": true,
      "seance_date": "2025-01-20"
    }
  ]
}
```

#### 1.3. Получение доступных дат
```http
GET /api/v1/book_dates/{company_id}?staff_id={staff_id}&service_ids[]={service_id}
```

**Параметры:**
- `staff_id` - ID сотрудника
- `service_ids[]` - массив ID услуг
- `date` - дата в рамках месяца (опционально)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "booking_dates": ["2025-01-20", "2025-01-21"],  // или timestamps
    "booking_days": {
      "1": [20, 21, 22],  // январь: дни 20, 21, 22
      "2": [1, 2, 3]      // февраль: дни 1, 2, 3
    },
    "working_dates": [...],
    "working_days": {...}
  }
}
```

#### 1.4. Получение доступного времени на конкретную дату
```http
GET /api/v1/book_times/{company_id}/{date}?staff_id={staff_id}&service_ids[]={service_id}
```

**Параметры:**
- `date` - дата в формате YYYY-MM-DD
- `staff_id` - ID сотрудника (0 если любой мастер)
- `service_ids[]` - массив ID услуг

**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "time": "10:00",
      "seance_length": 7200,
      "datetime": "2025-01-20T10:00:00+03:00"
    },
    {
      "time": "12:30",
      "seance_length": 7200,
      "datetime": "2025-01-20T12:30:00+03:00"
    }
  ]
}
```

#### 1.5. Получение ближайших сеансов
```http
GET /api/v1/book_seances/{company_id}/{staff_id}?service_ids[]={service_id}
```

**Параметры:**
- `service_ids[]` - массив ID услуг
- `datetime` - дата от которой искать (опционально)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "seance_date": "2025-01-20",
    "seances": [
      {
        "time": "10:00",
        "seance_length": 7200,
        "datetime": "2025-01-20T10:00:00+03:00"
      }
    ]
  }
}
```

### 2. Обязательные заголовки для запросов

```python
headers = {
    'Accept': 'application/vnd.yclients.v2+json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}',
    'X-Client-Id': 'fe2247033368a9cadab0c6c6f76172a9',  # Обязательный идентификатор партнера
    'User-Agent': 'YClientsClient/1.0'
}
```

### 3. Обработка ошибок

#### Ошибка 404 - Мастер недоступен для услуги
```json
{
  "success": false,
  "data": null,
  "meta": {
    "message": "Сотрудник недоступен для записи на выбранную услугу"
  }
}
```

**Возможные причины:**
- Мастер не оказывает выбранную услугу
- У мастера нет расписания на запрашиваемые даты
- Неверный ID мастера или услуги

#### Ошибка 401 - Проблемы с авторизацией
```json
{
  "success": false,
  "data": null,
  "meta": {
    "message": "Не указан идентификатор партнера"
  }
}
```

**Решение:** Добавить заголовок `X-Client-Id`

### 4. Рабочий пример на Python

```python
import httpx
import asyncio
from datetime import datetime

# Конфигурация
API_KEY = 'nmnsgmfcpdu65db2b5kp'
COMPANY_ID = '1297379'
BASE_URL = 'https://api.yclients.com/api/v1'

HEADERS = {
    'Accept': 'application/vnd.yclients.v2+json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}',
    'X-Client-Id': 'fe2247033368a9cadab0c6c6f76172a9',
}

async def get_available_slots(staff_id: int, service_id: int):
    """Получить все доступные слоты для мастера и услуги"""

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Получаем доступные даты
        dates_url = f"{BASE_URL}/book_dates/{COMPANY_ID}"
        dates_params = {
            'staff_id': staff_id,
            'service_ids[]': service_id
        }

        dates_response = await client.get(dates_url, headers=HEADERS, params=dates_params)

        if dates_response.status_code != 200:
            print(f"Ошибка получения дат: {dates_response.status_code}")
            return []

        dates_data = dates_response.json()
        if not dates_data.get('success'):
            print(f"API вернул ошибку: {dates_data}")
            return []

        booking_dates = dates_data.get('data', {}).get('booking_dates', [])

        if not booking_dates:
            print("Нет доступных дат")
            return []

        all_slots = []

        # 2. Для каждой даты получаем временные слоты
        for date in booking_dates:
            # Преобразуем дату в нужный формат
            if isinstance(date, (int, float)):
                date_obj = datetime.fromtimestamp(date)
                date_str = date_obj.strftime('%Y-%m-%d')
            else:
                date_str = date

            # Запрашиваем слоты на эту дату
            times_url = f"{BASE_URL}/book_times/{COMPANY_ID}/{date_str}"
            times_params = {
                'staff_id': staff_id,
                'service_ids[]': service_id
            }

            times_response = await client.get(times_url, headers=HEADERS, params=times_params)

            if times_response.status_code == 200:
                times_data = times_response.json()
                if times_data.get('success'):
                    slots = times_data.get('data', [])
                    for slot in slots:
                        all_slots.append({
                            'date': date_str,
                            'time': slot.get('time'),
                            'datetime': slot.get('datetime'),
                            'duration': slot.get('seance_length', 0) // 60  # в минутах
                        })

        return all_slots

# Использование
async def main():
    staff_id = 3884784  # ID мастера
    service_id = 19437973  # ID услуги

    slots = await get_available_slots(staff_id, service_id)

    print(f"Найдено слотов: {len(slots)}")
    for slot in slots:
        print(f"  • {slot['date']} {slot['time']} ({slot['duration']} мин)")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Интеграция в существующий код

В файле `core/yclients_client.py` уже реализованы методы:
- `get_available_days()` - получение доступных дат
- `get_available_times()` - получение временных слотов на дату
- `get_available_slots_for_staff()` - комбинированный метод для получения всех слотов

Эти методы корректно обрабатывают:
- Различные форматы дат (timestamps, ISO8601, YYYY-MM-DD)
- Ошибку недоступности мастера (404 с кодом STAFF_UNAVAILABLE)
- Кэширование результатов для оптимизации

### 6. Особенности API

1. **Формат параметров массивов**: При передаче массивов используется формат `param[]`, например: `service_ids[]`

2. **Формат дат**: API может возвращать даты в разных форматах:
   - Timestamps (Unix time)
   - ISO8601 строки
   - YYYY-MM-DD строки

3. **Обязательные заголовки**:
   - `X-Client-Id` - без него API возвращает ошибку 401
   - `Authorization: Bearer {token}` - токен авторизации

4. **Ограничения**:
   - Некоторые endpoint'ы могут быть недоступны для дат далеко в будущем
   - API может возвращать пустые результаты если у мастера нет расписания

### 7. Тестирование

Для тестирования API создан скрипт `test_yclients_api_slots.py`, который:
1. Получает список услуг
2. Находит доступных мастеров для услуги
3. Запрашивает доступные даты
4. Получает временные слоты
5. Проверяет метод ближайших сеансов

Скрипт успешно протестирован с реальным API и подтверждает работоспособность всех методов.

### 8. Рекомендации

1. **Всегда проверяйте поле `success` в ответе** - даже при статусе 200 API может вернуть ошибку
2. **Обрабатывайте 404 ошибки** - они часто означают, что мастер не оказывает услугу
3. **Используйте кэширование** - справочники услуг и мастеров меняются редко
4. **Проверяйте формат дат** - API может возвращать их в разных форматах

## Заключение

API YClients предоставляет полный набор методов для получения доступных слотов записи. Основная последовательность: услуги → мастера → даты → время. Все методы успешно протестированы и интегрированы в проект.
