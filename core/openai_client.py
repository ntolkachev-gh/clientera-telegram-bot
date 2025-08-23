"""
Core модули приложения
"""
import openai
import logging
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from config import settings
from database.models import OpenAIUsageLog, Client
from .yclients_client import YclientsClient
from .openai_tools import YclientsToolsDefinition, YclientsToolsHandler
from prompts import format_prompt, PromptNames

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Настройка OpenAI клиента
openai.api_key = settings.openai_api_key

# Настройки таймаутов для ускорения работы
OPENAI_TIMEOUTS = {
    "request_timeout": settings.openai_request_timeout if hasattr(settings, 'openai_request_timeout') else 30.0,
    "read_timeout": settings.openai_request_timeout if hasattr(settings, 'openai_request_timeout') else 30.0,
    "write_timeout": settings.openai_request_timeout if hasattr(settings, 'openai_request_timeout') else 30.0,
    "connect_timeout": settings.openai_connect_timeout if hasattr(settings, 'openai_connect_timeout') else 10.0,
    "pool_timeout": settings.openai_connect_timeout if hasattr(settings, 'openai_connect_timeout') else 10.0
}

# Цены на токены (в долларах за 1000 токенов) и характеристики скорости
PRICING = {
    "gpt-5": {"input": 0.005, "output": 0.015, "speed": "slow", "quality": "highest"},
    "gpt-4o": {"input": 0.005, "output": 0.015, "speed": "medium", "quality": "high"},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006, "speed": "fast", "quality": "good"},
    "gpt-4": {"input": 0.03, "output": 0.06, "speed": "slow", "quality": "high"},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03, "speed": "medium", "quality": "high"},
    "text-embedding-3-small": {"input": 0.0002, "output": 0.0, "speed": "fast", "quality": "good"}
}

# Характеристики моделей по скорости (в секундах на запрос)
MODEL_SPEED_CHARACTERISTICS = {
    "gpt-5": {"speed": "slow", "avg_response_time": 25.0, "recommendation": "Только для сложных задач"},
    "gpt-4o": {"speed": "medium", "avg_response_time": 8.0, "recommendation": "Сбалансированный выбор"},
    "gpt-4o-mini": {"speed": "fast", "avg_response_time": 3.0, "recommendation": "Рекомендуется для скорости"},
    "gpt-4": {"speed": "slow", "avg_response_time": 15.0, "recommendation": "Устаревшая, медленная"},
    "gpt-4-turbo": {"speed": "medium", "avg_response_time": 10.0, "recommendation": "Средняя скорость"}
}


class OpenAIClient:
    def __init__(self, db: Session, yclients_client: Optional[YclientsClient] = None):
        self.db = db

        # Проверяем корректность определения моделей
        self._validate_model_definitions()

        # Инициализация клиента с таймаутами для ускорения работы
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            timeout=OPENAI_TIMEOUTS["request_timeout"]
        )
        self.yclients = yclients_client

        # Инициализация tools если доступен yclients клиент
        if yclients_client:
            self.available_tools = YclientsToolsDefinition.get_tools_schema()
            self.tools_handler = YclientsToolsHandler(yclients_client)
            self.tool_functions = self.tools_handler.get_tool_functions()
        else:
            self.available_tools = []
            self.tools_handler = None
            self.tool_functions = {}

    def _validate_model_definitions(self):
        """Проверка корректности определения моделей"""
        required_keys = ["speed", "avg_response_time", "recommendation"]

        for model_name, model_data in MODEL_SPEED_CHARACTERISTICS.items():
            missing_keys = [key for key in required_keys if key not in model_data]
            if missing_keys:
                logger.error(f"❌ Модель '{model_name}' не содержит ключи: {missing_keys}")
                logger.error(f"📊 Текущие данные: {model_data}")
            else:
                logger.debug(f"✅ Модель '{model_name}' корректно определена")

    def select_model_for_task(self, task_complexity: str = "medium") -> str:
        """
        Выбор модели в зависимости от сложности задачи

        Args:
            task_complexity: "simple", "medium", "complex"

        Returns:
            Название модели
        """
        if getattr(settings, 'use_fast_model_by_default', True):
            if task_complexity == "simple":
                return getattr(settings, 'openai_fast_model', 'gpt-4o-mini')
            elif task_complexity == "medium":
                return getattr(settings, 'openai_balanced_model', 'gpt-4o')
            else:  # complex
                return getattr(settings, 'openai_quality_model', 'gpt-5')
        else:
            return settings.openai_default_model

    def get_model_info(self, model: str) -> dict:
        """Получение информации о модели"""
        logger.debug(f"🔍 Получение информации о модели: {model}")
        logger.debug(f"📊 Доступные модели: {list(MODEL_SPEED_CHARACTERISTICS.keys())}")

        if model in MODEL_SPEED_CHARACTERISTICS:
            model_data = MODEL_SPEED_CHARACTERISTICS[model]
            logger.debug(f"✅ Модель найдена: {model_data}")
            return {
                "model": model,
                "speed": model_data.get("speed", "unknown"),
                "avg_response_time": model_data.get("avg_response_time", 0),
                "recommendation": model_data.get("recommendation", "Нет данных"),
                "cost_per_1k_tokens": PRICING.get(model, {}).get("input", 0)
            }
        else:
            # Безопасная обработка для неизвестных моделей
            logger.warning(f"⚠️ Модель '{model}' не найдена в справочнике. Доступные: {list(MODEL_SPEED_CHARACTERISTICS.keys())}")
            return {
                "model": model,
                "speed": "unknown",
                "avg_response_time": 0,
                "recommendation": "Модель не найдена в справочнике",
                "cost_per_1k_tokens": PRICING.get(model, {}).get("input", 0)
            }

    def _log_usage(self, client_id: Optional[int], model: str, purpose: str,
                   prompt_tokens: int, completion_tokens: int, total_tokens: int):
        """Логирование использования OpenAI API"""
        cost = 0.0
        speed_info = ""
        if model in PRICING:
            cost = (prompt_tokens * PRICING[model]["input"] +
                   completion_tokens * PRICING[model]["output"]) / 1000

            if model in MODEL_SPEED_CHARACTERISTICS:
                model_data = MODEL_SPEED_CHARACTERISTICS[model]
                speed_info = f" | Скорость: {model_data.get('speed', 'unknown')} ({model_data.get('avg_response_time', 0):.1f}s)"

        logger.info(f"💰 OpenAI использование - Модель: {model}, Цель: {purpose}, "
                   f"Токенов: {total_tokens} (вход: {prompt_tokens}, выход: {completion_tokens}), "
                   f"Стоимость: ${cost:.4f}{speed_info}")

        usage_log = OpenAIUsageLog(
            client_id=client_id,
            model=model,
            purpose=purpose,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost
        )
        self.db.add(usage_log)
        self.db.commit()

    async def chat_completion(self, messages: List[Dict[str, str]],
                            client_id: Optional[int] = None,
                            model: str = None) -> str:
        """Получение ответа от GPT модели"""
        if model is None:
            model = settings.openai_default_model

        logger.info(f"🤖 Отправка запроса в OpenAI - Модель: {model}, Клиент: {client_id}")
        try:
            # Параметры для разных моделей
            if model.startswith("gpt-5"):
                # GPT-5 не поддерживает temperature и max_tokens
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=OPENAI_TIMEOUTS["request_timeout"]
                )
            else:
                # GPT-4o, GPT-4 и другие модели поддерживают все параметры
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                    timeout=OPENAI_TIMEOUTS["request_timeout"]
                )

            # Логирование использования
            usage = response.usage
            self._log_usage(
                client_id=client_id,
                model=model,
                purpose="chat",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )

            response_content = response.choices[0].message.content
            logger.info(f"✅ Получен ответ от OpenAI: {response_content[:100]}...")
            return response_content

        except Exception as e:
            logger.error(f"❌ Ошибка при обращении к OpenAI: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."

    async def extract_facts(self, conversation_history: str,
                          client_id: Optional[int] = None) -> Dict[str, Any]:
        """Извлечение фактов о клиенте из истории разговора"""
        try:
            prompt = format_prompt(
                PromptNames.FACT_EXTRACTION,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: не удалось загрузить промпт для извлечения фактов: {e}")
            return {
                "favorite_services": [],
                "favorite_masters": [],
                "preferred_time_slots": [],
                "custom_notes": {
                    "allergies": "",
                    "preferences": "",
                    "other": "Ошибка при анализе разговора"
                }
            }

        try:
            # Параметры для разных моделей
            if settings.openai_default_model.startswith("gpt-5"):
                response = self.client.chat.completions.create(
                    model=settings.openai_default_model,
                    messages=[{"role": "user", "content": prompt}]
                )
            else:
                response = self.client.chat.completions.create(
                    model=settings.openai_default_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )

            # Логирование использования
            usage = response.usage
            self._log_usage(
                client_id=client_id,
                model=settings.openai_default_model,
                purpose="fact_extraction",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении фактов: {e}")
            return {}

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для текстов"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
                timeout=OPENAI_TIMEOUTS["request_timeout"]
            )

            # Логирование использования
            total_tokens = response.usage.total_tokens
            self._log_usage(
                client_id=None,
                model="text-embedding-3-small",
                purpose="embedding",
                prompt_tokens=total_tokens,
                completion_tokens=0,
                total_tokens=total_tokens
            )

            return [embedding.embedding for embedding in response.data]

        except Exception as e:
            logger.error(f"❌ Ошибка при создании эмбеддингов: {e}")
            return []

    async def process_booking_request(self, user_message: str,
                                    client_profile: Dict[str, Any],
                                    available_services: Optional[List[str]] = None,
                                    use_tools: bool = True) -> Dict[str, Any]:
        """Обработка запроса на запись с учетом профиля клиента"""

        # Если доступны tools, используем их для более точной обработки
        if use_tools and self.yclients and self.available_tools:
            logger.info("🔧 Используем tools для обработки запроса на запись")

            try:
                system_prompt = format_prompt(
                    PromptNames.SALON_ASSISTANT_SYSTEM,
                    favorite_services=client_profile.get('favorite_services', []),
                    favorite_masters=client_profile.get('favorite_masters', []),
                    preferred_time_slots=client_profile.get('preferred_time_slots', [])
                )
            except Exception as e:
                logger.error(f"❌ Критическая ошибка: не удалось загрузить системный промпт: {e}")
                return {
                    "intent": "other",
                    "confidence": 0.0,
                    "response": "Извините, произошла техническая ошибка. Попробуйте позже.",
                    "used_tools": False,
                    "error": "Ошибка загрузки промпта"
                }

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            try:
                response_text = await self.chat_completion_with_tools(
                    messages=messages,
                    client_id=client_profile.get('id'),
                    model=settings.openai_default_model
                )

                # Определяем intent на основе ответа
                intent = "booking" if any(keyword in user_message.lower() for keyword in
                    ["записаться", "запись", "хочу записаться", "записаться на", "записаться к"]) else "question"

                return {
                    "intent": intent,
                    "confidence": 0.9,
                    "response": response_text,
                    "used_tools": True
                }

            except Exception as e:
                logger.error(f"❌ Ошибка при использовании tools: {e}")
                # Fallback к старому методу
                use_tools = False

        # Старый метод без tools
        logger.info("📝 Используем стандартный анализ запроса без tools")

        # Добавляем список услуг, известный боту (если передан)
        services_list_text = ", ".join(available_services) if available_services else "неизвестно"

        try:
            prompt = format_prompt(
                PromptNames.BOOKING_ANALYSIS,
                user_message=user_message,
                favorite_services=client_profile.get('favorite_services', []),
                favorite_masters=client_profile.get('favorite_masters', []),
                preferred_time_slots=client_profile.get('preferred_time_slots', []),
                services_list=services_list_text
            )
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: не удалось загрузить промпт для анализа бронирования: {e}")
            return {
                "intent": "other",
                "confidence": 0.0,
                "response": "Извините, произошла техническая ошибка. Попробуйте позже.",
                "error": "Ошибка загрузки промпта"
            }

        try:
            # Параметры для разных моделей
            if settings.openai_default_model.startswith("gpt-5"):
                response = self.client.chat.completions.create(
                    model=settings.openai_default_model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=OPENAI_TIMEOUTS["request_timeout"]
                )
            else:
                response = self.client.chat.completions.create(
                    model=settings.openai_default_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3,
                    timeout=OPENAI_TIMEOUTS["request_timeout"]
                )

            # Логирование использования
            usage = response.usage
            self._log_usage(
                client_id=client_profile.get('id'),
                model=settings.openai_default_model,
                purpose="booking_analysis",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )

            result = json.loads(response.choices[0].message.content)

            # Добавляем логирование для отладки
            logger.info(f"🔍 Анализ запроса: '{user_message}' -> intent: {result.get('intent')}")

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке запроса на запись: {e}")
            return {
                "intent": "other",
                "confidence": 0.0,
                "response": "Извините, произошла ошибка при обработке вашего запроса."
            }

    # ============================================================================
    # ОСНОВНОЙ МЕТОД С ПОДДЕРЖКОЙ TOOLS
    # ============================================================================

    async def chat_completion_with_tools(self, messages: List[Dict[str, str]],
                                       client_id: Optional[int] = None,
                                       model: str = None,
                                       max_tool_calls: int = None) -> str:
        """
        Получение ответа от GPT модели с поддержкой function calling

        Args:
            messages: список сообщений для диалога
            client_id: ID клиента для логирования
            model: модель OpenAI
            max_tool_calls: максимальное количество вызовов tools

        Returns:
            Итоговый ответ модели
        """
        start_time = datetime.now()
        if max_tool_calls is None:
            max_tool_calls = getattr(settings, 'openai_max_tool_calls', 3)

        if not self.yclients or not self.available_tools:
            logger.warning("⚠️ Tools не доступны, используем обычный chat_completion")
            return await self.chat_completion(messages, client_id, model)

        if model is None:
            # Используем быструю модель по умолчанию для ускорения
            if getattr(settings, 'use_fast_model_by_default', True):
                model = getattr(settings, 'openai_fast_model', 'gpt-4o-mini')
                logger.info(f"🚀 Используем быструю модель по умолчанию: {model}")
            else:
                model = settings.openai_default_model

        # Дополнительная проверка модели
        logger.info(f"🔍 Проверяем модель: '{model}' (тип: {type(model)})")
        if not isinstance(model, str):
            logger.error(f"❌ Некорректный тип модели: {type(model)}, значение: {model}")
            model = "gpt-4o-mini"  # Fallback к безопасной модели
            logger.info(f"🔄 Используем fallback модель: {model}")

        logger.info(f"🤖 Отправка запроса в OpenAI с tools - Модель: {model}, Клиент: {client_id}")
        logger.info(f"🔧 Доступно tools: {len(self.available_tools)}")
        logger.info(f"⏱️ Максимум итераций: {max_tool_calls}")

        # Логируем информацию о выбранной модели
        try:
            model_info = self.get_model_info(model)
            logger.info(f"📊 Модель: {model_info['model']} | Скорость: {model_info['speed']} | "
                       f"Ожидаемое время: {model_info['avg_response_time']:.1f}s | "
                       f"Рекомендация: {model_info['recommendation']}")
        except Exception as e:
            logger.error(f"❌ Ошибка при получении информации о модели '{model}': {e}")
            # Используем безопасные значения по умолчанию
            model_info = {
                "model": model,
                "speed": "unknown",
                "avg_response_time": 0,
                "recommendation": "Ошибка получения данных"
            }

        try:
            tool_calls_count = 0
            current_messages = messages.copy()

            while tool_calls_count < max_tool_calls:
                # Отправляем запрос с tools
                if model.startswith("gpt-5"):
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=current_messages,
                        tools=self.available_tools,
                        tool_choice="auto",
                        timeout=OPENAI_TIMEOUTS["request_timeout"]
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=current_messages,
                        tools=self.available_tools,
                        tool_choice="auto",
                        max_tokens=1000,
                        temperature=0.7,
                        timeout=OPENAI_TIMEOUTS["request_timeout"]
                    )

                # Логирование использования
                usage = response.usage
                self._log_usage(
                    client_id=client_id,
                    model=model,
                    purpose="chat_with_tools",
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens
                )

                message = response.choices[0].message

                # Добавляем ответ модели к истории
                current_messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in (message.tool_calls or [])
                    ] if message.tool_calls else None
                })

                # Если нет вызовов функций, возвращаем ответ
                if not message.tool_calls:
                    logger.info(f"✅ Получен финальный ответ от OpenAI: {message.content[:100]}...")
                    return message.content or "Извините, не удалось получить ответ."

                # Обрабатываем вызовы функций параллельно
                logger.info(f"🔧 Модель запросила {len(message.tool_calls)} tool(s)")
                logger.info("🚀 Запускаем parallel tool calling...")

                # Создаем задачи для параллельного выполнения
                async def execute_tool_call(tool_call):
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"📞 Параллельный вызов функции: {function_name}({function_args})")

                    # Вызываем соответствующую функцию
                    if function_name in self.tool_functions:
                        try:
                            tool_result = await self.tool_functions[function_name](**function_args)
                            logger.info(f"📋 Результат {function_name}: {str(tool_result)[:200]}...")
                            return tool_call.id, tool_result
                        except Exception as e:
                            logger.error(f"❌ Ошибка при вызове {function_name}: {e}")
                            return tool_call.id, {"error": f"Ошибка выполнения функции: {str(e)}", "success": False}
                    else:
                        logger.error(f"❌ Неизвестная функция: {function_name}")
                        return tool_call.id, {"error": f"Неизвестная функция: {function_name}", "success": False}

                # Запускаем все tool calls параллельно
                tasks = [execute_tool_call(tool_call) for tool_call in message.tool_calls]
                tool_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Обрабатываем результаты
                for i, result in enumerate(tool_results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Исключение при выполнении tool call: {result}")
                        tool_call_id = message.tool_calls[i].id
                        tool_result = {"error": f"Исключение: {str(result)}", "success": False}
                    else:
                        tool_call_id, tool_result = result

                    # Добавляем результат функции к истории
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

                logger.info(f"✅ Завершено параллельное выполнение {len(message.tool_calls)} tool(s)")

                tool_calls_count += 1
                logger.info(f"🔄 Итерация {tool_calls_count}, продолжаем диалог...")

            # Если достигли лимита вызовов
            logger.warning(f"⚠️ Достигнут лимит вызовов tools ({max_tool_calls})")
            return "Извините, не удалось обработать ваш запрос полностью. Попробуйте упростить вопрос."

        except Exception as e:
            logger.error(f"❌ Ошибка при обращении к OpenAI с tools: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."
        finally:
            # Логируем общее время выполнения
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            logger.info(f"⏱️ Общее время выполнения: {total_time:.2f} секунд")
            logger.info(f"📊 Модель {model} показала {'быструю' if total_time < 10 else 'среднюю' if total_time < 20 else 'медленную'} производительность")
