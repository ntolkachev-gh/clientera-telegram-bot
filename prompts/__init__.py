"""
Модуль для работы с промптами
"""
import os
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptLoader:
    """Класс для загрузки промптов из файлов"""

    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            # Определяем путь к папке prompts относительно текущего файла
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.prompts_dir = current_dir
        else:
            self.prompts_dir = prompts_dir

        # Кэш для загруженных промптов
        self._cache = {}

        logger.info(f"📁 PromptLoader инициализирован: {self.prompts_dir}")

    def load_prompt(self, prompt_name: str) -> str:
        """
        Загрузить промпт из файла

        Args:
            prompt_name: имя файла промпта без расширения

        Returns:
            Содержимое промпта
        """
        # Проверяем кэш
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        file_path = os.path.join(self.prompts_dir, f"{prompt_name}.txt")

        if not os.path.exists(file_path):
            logger.error(f"❌ Файл промпта не найден: {file_path}")
            raise FileNotFoundError(f"Промпт файл не найден: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # Кэшируем содержимое
            self._cache[prompt_name] = content

            logger.info(f"📋 Загружен промпт: {prompt_name} ({len(content)} символов)")
            return content

        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке промпта {prompt_name}: {e}")
            raise

    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Загрузить и отформатировать промпт

        Args:
            prompt_name: имя файла промпта
            **kwargs: переменные для форматирования

        Returns:
            Отформатированный промпт
        """
        template = self.load_prompt(prompt_name)

        # Автоматически добавляем текущую дату для системных промптов
        if prompt_name in [PromptNames.SALON_ASSISTANT_SYSTEM, PromptNames.BOOKING_ANALYSIS, PromptNames.FACT_EXTRACTION]:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M")
            current_day = datetime.now().strftime("%A")  # День недели на английском

            # Русские названия дней недели
            russian_days = {
                "Monday": "Понедельник",
                "Tuesday": "Вторник",
                "Wednesday": "Среда",
                "Thursday": "Четверг",
                "Friday": "Пятница",
                "Saturday": "Суббота",
                "Sunday": "Воскресенье"
            }

            current_day_ru = russian_days.get(current_day, current_day)

            # Добавляем дату в kwargs если её там нет
            if 'current_date' not in kwargs:
                kwargs['current_date'] = current_date
            if 'current_time' not in kwargs:
                kwargs['current_time'] = current_time
            if 'current_day' not in kwargs:
                kwargs['current_day'] = current_day_ru

        try:
            formatted = template.format(**kwargs)
            logger.debug(f"✅ Промпт {prompt_name} отформатирован с параметрами: {list(kwargs.keys())}")
            return formatted
        except KeyError as e:
            logger.error(f"❌ Отсутствует параметр для форматирования промпта {prompt_name}: {e}")
            raise ValueError(f"Отсутствует параметр {e} для промпта {prompt_name}")

    def clear_cache(self):
        """Очистить кэш промптов"""
        self._cache.clear()
        logger.info("🗑️ Кэш промптов очищен")

    def list_prompts(self) -> list:
        """Получить список доступных промптов"""
        try:
            files = os.listdir(self.prompts_dir)
            prompts = [f[:-4] for f in files if f.endswith('.txt')]
            logger.info(f"📋 Найдено промптов: {len(prompts)}")
            return prompts
        except Exception as e:
            logger.error(f"❌ Ошибка при получении списка промптов: {e}")
            return []


# Глобальный экземпляр для удобства использования
prompt_loader = PromptLoader()


# Удобные функции для быстрого доступа
def load_prompt(prompt_name: str) -> str:
    """Загрузить промпт"""
    return prompt_loader.load_prompt(prompt_name)


def format_prompt(prompt_name: str, **kwargs) -> str:
    """Загрузить и отформатировать промпт"""
    return prompt_loader.format_prompt(prompt_name, **kwargs)


# Константы с именами промптов для избежания опечаток
class PromptNames:
    """Константы с именами промптов"""
    SALON_ASSISTANT_SYSTEM = "salon_assistant_system"
    FACT_EXTRACTION = "fact_extraction"
    BOOKING_ANALYSIS = "booking_analysis"
