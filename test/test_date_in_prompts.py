"""
Тест для проверки автоматического добавления текущей даты в промпты
"""
import sys
import os
from datetime import datetime

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import format_prompt, PromptNames


def test_date_in_salon_assistant_system():
    """Тест добавления даты в системный промпт салонного ассистента"""
    print("🧪 Тестируем добавление даты в salon_assistant_system...")

    try:
        formatted_prompt = format_prompt(
            PromptNames.SALON_ASSISTANT_SYSTEM,
            favorite_services="стрижка, окрашивание",
            favorite_masters="Анна, Мария",
            preferred_time_slots="вечер"
        )

        # Проверяем, что дата добавлена
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")

        if current_date in formatted_prompt:
            print(f"✅ Дата {current_date} успешно добавлена в промпт")
        else:
            print(f"❌ Дата {current_date} не найдена в промпте")

        if current_day in formatted_prompt:
            print(f"✅ День недели {current_day} успешно добавлен в промпт")
        else:
            print(f"❌ День недели {current_day} не найден в промпте")

        print("📋 Первые 200 символов промпта:")
        print(formatted_prompt[:200] + "...")

        return True

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False


def test_date_in_booking_analysis():
    """Тест добавления даты в промпт анализа бронирования"""
    print("\n🧪 Тестируем добавление даты в booking_analysis...")

    try:
        formatted_prompt = format_prompt(
            PromptNames.BOOKING_ANALYSIS,
            user_message="Хочу записаться на стрижку",
            favorite_services="стрижка",
            favorite_masters="Анна",
            preferred_time_slots="вечер",
            services_list="стрижка, окрашивание, маникюр"
        )

        # Проверяем, что дата добавлена
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")

        if current_date in formatted_prompt:
            print(f"✅ Дата {current_date} успешно добавлена в промпт")
        else:
            print(f"❌ Дата {current_date} не найдена в промпте")

        if current_day in formatted_prompt:
            print(f"✅ День недели {current_day} успешно добавлен в промпт")
        else:
            print(f"❌ День недели {current_day} не найден в промпте")

        print("📋 Первые 200 символов промпта:")
        print(formatted_prompt[:200] + "...")

        return True

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False


def test_date_in_fact_extraction():
    """Тест добавления даты в промпт извлечения фактов"""
    print("\n🧪 Тестируем добавление даты в fact_extraction...")

    try:
        formatted_prompt = format_prompt(
            PromptNames.FACT_EXTRACTION,
            conversation_history="Клиент хочет записаться на стрижку к мастеру Анне"
        )

        # Проверяем, что дата добавлена
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")

        if current_date in formatted_prompt:
            print(f"✅ Дата {current_date} успешно добавлена в промпт")
        else:
            print(f"❌ Дата {current_date} не найдена в промпте")

        if current_day in formatted_prompt:
            print(f"✅ День недели {current_day} успешно добавлен в промпт")
        else:
            print(f"❌ День недели {current_day} не найден в промпте")

        print("📋 Первые 200 символов промпта:")
        print(formatted_prompt[:200] + "...")

        return True

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False


def test_manual_date_override():
    """Тест переопределения даты вручную"""
    print("\n🧪 Тестируем переопределение даты вручную...")

    try:
        custom_date = "2024-12-25"
        custom_day = "Среда"

        formatted_prompt = format_prompt(
            PromptNames.SALON_ASSISTANT_SYSTEM,
            favorite_services="стрижка",
            favorite_masters="Анна",
            preferred_time_slots="утро",
            current_date=custom_date,
            current_day=custom_day
        )

        if custom_date in formatted_prompt:
            print(f"✅ Кастомная дата {custom_date} успешно применена")
        else:
            print(f"❌ Кастомная дата {custom_date} не найдена в промпте")

        if custom_day in formatted_prompt:
            print(f"✅ Кастомный день {custom_day} успешно применен")
        else:
            print(f"❌ Кастомный день {custom_day} не найден в промпте")

        return True

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов для проверки добавления даты в промпты\n")

    tests = [
        test_date_in_salon_assistant_system,
        test_date_in_booking_analysis,
        test_date_in_fact_extraction,
        test_manual_date_override
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("⚠️ Некоторые тесты не прошли")
        return 1


if __name__ == "__main__":
    exit(main())
