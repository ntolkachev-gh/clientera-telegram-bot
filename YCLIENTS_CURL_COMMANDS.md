# YClients API - Рабочие CURL команды для получения слотов

## Базовые параметры

```bash
# Константы
API_KEY="nmnsgmfcpdu65db2b5kp"
COMPANY_ID="1297379"
BASE_URL="https://api.yclients.com/api/v1"
CLIENT_ID="fe2247033368a9cadab0c6c6f76172a9"
```

## 1. Получение списка услуг

```bash
curl -X GET "${BASE_URL}/book_services/${COMPANY_ID}" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "User-Agent: YClientsClient/1.0"
```

**Готовая команда:**
```bash
curl -X GET "https://api.yclients.com/api/v1/book_services/1297379" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" \
  --header "User-Agent: YClientsClient/1.0"
```

## 2. Получение списка мастеров

### Все мастера
```bash
curl -X GET "${BASE_URL}/book_staff/${COMPANY_ID}" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "User-Agent: YClientsClient/1.0"
```

### Мастера для конкретной услуги
```bash
curl -X GET "${BASE_URL}/book_staff/${COMPANY_ID}?service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "User-Agent: YClientsClient/1.0"
```

**Готовая команда:**
```bash
curl -X GET "https://api.yclients.com/api/v1/book_staff/1297379?service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" \
  --header "User-Agent: YClientsClient/1.0"
```

## 3. Получение доступных дат

```bash
curl -X GET "${BASE_URL}/book_dates/${COMPANY_ID}?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "User-Agent: YClientsClient/1.0"
```

**Готовая команда:**
```bash
curl -X GET "https://api.yclients.com/api/v1/book_dates/1297379?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" \
  --header "User-Agent: YClientsClient/1.0"
```

## 4. Получение доступного времени на дату

```bash
curl -X GET "${BASE_URL}/book_times/${COMPANY_ID}/2025-01-20?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "User-Agent: YClientsClient/1.0"
```

**Готовая команда (на сегодняшнюю дату):**
```bash
curl -X GET "https://api.yclients.com/api/v1/book_times/1297379/$(date +%Y-%m-%d)?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" \
  --header "User-Agent: YClientsClient/1.0"
```

**Готовая команда (на конкретную дату):**
```bash
curl -X GET "https://api.yclients.com/api/v1/book_times/1297379/2025-01-20?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" \
  --header "User-Agent: YClientsClient/1.0"
```

## 5. Получение ближайших сеансов

```bash
curl -X GET "${BASE_URL}/book_seances/${COMPANY_ID}/3884784?service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "User-Agent: YClientsClient/1.0"
```

**Готовая команда:**
```bash
curl -X GET "https://api.yclients.com/api/v1/book_seances/1297379/3884784?service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" \
  --header "User-Agent: YClientsClient/1.0"
```

## 6. Полный сценарий поиска слотов

### Шаг 1: Получаем услуги
```bash
echo "=== 1. Получение услуг ==="
curl -s -X GET "https://api.yclients.com/api/v1/book_services/1297379" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" | jq '.data.services[] | {id: .id, title: .title, price_min: .price_min}' | head -20
```

### Шаг 2: Получаем мастеров для услуги
```bash
echo "=== 2. Получение мастеров для услуги 19437973 ==="
curl -s -X GET "https://api.yclients.com/api/v1/book_staff/1297379?service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" | jq '.data[] | {id: .id, name: .name, specialization: .specialization, bookable: .bookable}'
```

### Шаг 3: Получаем доступные даты
```bash
echo "=== 3. Получение доступных дат для мастера 3884784 ==="
curl -s -X GET "https://api.yclients.com/api/v1/book_dates/1297379?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" | jq '.data'
```

### Шаг 4: Получаем время на конкретную дату
```bash
echo "=== 4. Получение времени на дату 2025-01-20 ==="
curl -s -X GET "https://api.yclients.com/api/v1/book_times/1297379/2025-01-20?staff_id=3884784&service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" | jq '.data[] | {time: .time, datetime: .datetime, duration_min: (.seance_length / 60)}'
```

### Шаг 5: Получаем ближайшие сеансы
```bash
echo "=== 5. Получение ближайших сеансов ==="
curl -s -X GET "https://api.yclients.com/api/v1/book_seances/1297379/3884784?service_ids[]=19437973" \
  --header "Accept: application/vnd.yclients.v2+json" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9" | jq '.'
```

## 7. Bash скрипт для полного поиска слотов

```bash
#!/bin/bash

# Конфигурация
API_KEY="nmnsgmfcpdu65db2b5kp"
COMPANY_ID="1297379"
BASE_URL="https://api.yclients.com/api/v1"
CLIENT_ID="fe2247033368a9cadab0c6c6f76172a9"

# Заголовки
HEADERS=(
  --header "Accept: application/vnd.yclients.v2+json"
  --header "Content-Type: application/json"
  --header "Authorization: Bearer ${API_KEY}"
  --header "X-Client-Id: ${CLIENT_ID}"
  --header "User-Agent: YClientsClient/1.0"
)

echo "🔍 YClients API - Поиск доступных слотов"
echo "========================================"

# 1. Получаем услуги
echo -e "\n📋 1. Получение услуг..."
SERVICES=$(curl -s -X GET "${BASE_URL}/book_services/${COMPANY_ID}" "${HEADERS[@]}")
echo "$SERVICES" | jq -r '.data.services[0:3][] | "ID: \(.id) - \(.title) (\(.price_min)₽)"'

# Берем первую услугу
SERVICE_ID=$(echo "$SERVICES" | jq -r '.data.services[0].id')
SERVICE_NAME=$(echo "$SERVICES" | jq -r '.data.services[0].title')
echo "🎯 Выбрана услуга: $SERVICE_NAME (ID: $SERVICE_ID)"

# 2. Получаем мастеров для услуги
echo -e "\n👥 2. Получение мастеров для услуги..."
STAFF=$(curl -s -X GET "${BASE_URL}/book_staff/${COMPANY_ID}?service_ids[]=${SERVICE_ID}" "${HEADERS[@]}")
echo "$STAFF" | jq -r '.data[] | select(.bookable == true) | "ID: \(.id) - \(.name) (\(.specialization))"'

# Берем первого доступного мастера
STAFF_ID=$(echo "$STAFF" | jq -r '.data[] | select(.bookable == true) | .id' | head -1)
STAFF_NAME=$(echo "$STAFF" | jq -r '.data[] | select(.bookable == true) | .name' | head -1)

if [ "$STAFF_ID" = "null" ] || [ -z "$STAFF_ID" ]; then
    echo "❌ Нет доступных мастеров для услуги"
    exit 1
fi

echo "🎯 Выбран мастер: $STAFF_NAME (ID: $STAFF_ID)"

# 3. Получаем доступные даты
echo -e "\n📅 3. Получение доступных дат..."
DATES=$(curl -s -X GET "${BASE_URL}/book_dates/${COMPANY_ID}?staff_id=${STAFF_ID}&service_ids[]=${SERVICE_ID}" "${HEADERS[@]}")

# Проверяем на ошибки
if echo "$DATES" | jq -e '.success == false' > /dev/null; then
    echo "❌ Ошибка получения дат:"
    echo "$DATES" | jq -r '.meta.message'
    exit 1
fi

BOOKING_DATES=$(echo "$DATES" | jq -r '.data.booking_dates[]' 2>/dev/null)
if [ -z "$BOOKING_DATES" ]; then
    echo "❌ Нет доступных дат"
    exit 1
fi

echo "✅ Найдено дат: $(echo "$BOOKING_DATES" | wc -l)"
echo "$BOOKING_DATES" | head -5

# Берем первую дату
FIRST_DATE=$(echo "$BOOKING_DATES" | head -1)

# Если дата в формате timestamp, конвертируем
if [[ "$FIRST_DATE" =~ ^[0-9]+$ ]]; then
    FIRST_DATE=$(date -r "$FIRST_DATE" +%Y-%m-%d 2>/dev/null || date -d "@$FIRST_DATE" +%Y-%m-%d 2>/dev/null)
fi

echo "🎯 Выбрана дата: $FIRST_DATE"

# 4. Получаем время на выбранную дату
echo -e "\n🕐 4. Получение времени на дату $FIRST_DATE..."
TIMES=$(curl -s -X GET "${BASE_URL}/book_times/${COMPANY_ID}/${FIRST_DATE}?staff_id=${STAFF_ID}&service_ids[]=${SERVICE_ID}" "${HEADERS[@]}")

# Проверяем результат
if echo "$TIMES" | jq -e '.success == false' > /dev/null; then
    echo "❌ Ошибка получения времени:"
    echo "$TIMES" | jq -r '.meta.message'
else
    TIME_SLOTS=$(echo "$TIMES" | jq -r '.data[]? | "\(.time) (\(.seance_length / 60 | floor) мин)"' 2>/dev/null)
    if [ -z "$TIME_SLOTS" ]; then
        echo "❌ Нет доступных временных слотов на эту дату"
    else
        echo "✅ Найдено слотов: $(echo "$TIME_SLOTS" | wc -l)"
        echo "$TIME_SLOTS"
    fi
fi

# 5. Получаем ближайшие сеансы как альтернативу
echo -e "\n🎯 5. Получение ближайших сеансов..."
SEANCES=$(curl -s -X GET "${BASE_URL}/book_seances/${COMPANY_ID}/${STAFF_ID}?service_ids[]=${SERVICE_ID}" "${HEADERS[@]}")

if echo "$SEANCES" | jq -e '.success == true' > /dev/null; then
    SEANCE_DATE=$(echo "$SEANCES" | jq -r '.data.seance_date // empty')
    if [ -n "$SEANCE_DATE" ]; then
        echo "✅ Ближайшая дата с сеансами: $SEANCE_DATE"
        echo "$SEANCES" | jq -r '.data.seances[]? | "\(.time) (\(.seance_length / 60 | floor) мин)"'
    else
        echo "❌ Нет ближайших сеансов"
    fi
else
    echo "❌ Ошибка получения ближайших сеансов"
fi

echo -e "\n✅ Анализ завершен!"
```

## 8. Команды для тестирования с обработкой ошибок

### Тест с красивым выводом
```bash
# Функция для выполнения запроса с обработкой ошибок
test_api() {
    local url="$1"
    local description="$2"

    echo -e "\n🔍 $description"
    echo "URL: $url"

    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "$url" \
        --header "Accept: application/vnd.yclients.v2+json" \
        --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
        --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9")

    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    json_data=$(echo "$response" | sed '/HTTP_STATUS:/d')

    echo "Статус: $http_status"

    if [ "$http_status" = "200" ]; then
        if echo "$json_data" | jq -e '.success == true' > /dev/null 2>&1; then
            echo "✅ Успешно"
            echo "$json_data" | jq '.' | head -20
        else
            echo "❌ API вернул ошибку"
            echo "$json_data" | jq '.meta.message // "Неизвестная ошибка"'
        fi
    else
        echo "❌ HTTP ошибка $http_status"
        echo "$json_data" | jq '.meta.message // "Неизвестная ошибка"' 2>/dev/null || echo "$json_data"
    fi
}

# Тестируем все endpoints
test_api "https://api.yclients.com/api/v1/book_services/1297379" "Получение услуг"
test_api "https://api.yclients.com/api/v1/book_staff/1297379?service_ids[]=19437973" "Получение мастеров"
test_api "https://api.yclients.com/api/v1/book_dates/1297379?staff_id=3884784&service_ids[]=19437973" "Получение дат"
test_api "https://api.yclients.com/api/v1/book_times/1297379/$(date +%Y-%m-%d)?staff_id=3884784&service_ids[]=19437973" "Получение времени"
```

## 9. Параметры для разных сценариев

### Множественные услуги
```bash
curl -X GET "https://api.yclients.com/api/v1/book_staff/1297379?service_ids[]=19437973&service_ids[]=19437982" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9"
```

### Фильтр по дате
```bash
curl -X GET "https://api.yclients.com/api/v1/book_dates/1297379?staff_id=3884784&service_ids[]=19437973&date=$(date +%Y-%m-%d)" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9"
```

### Любой мастер (staff_id=0)
```bash
curl -X GET "https://api.yclients.com/api/v1/book_times/1297379/$(date +%Y-%m-%d)?staff_id=0&service_ids[]=19437973" \
  --header "Authorization: Bearer nmnsgmfcpdu65db2b5kp" \
  --header "X-Client-Id: fe2247033368a9cadab0c6c6f76172a9"
```

Все команды протестированы и готовы к использованию!

