#!/usr/bin/env python3
"""
Скрипт для запуска демо-напоминаний с настройками
"""

import asyncio
import sys
import os
import argparse

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.demo_reminder import DemoReminderSystem

async def run_demo(interval_minutes: int = 15, duration_hours: int = None):
    """Запуск демо-напоминаний"""
    print(f"🚀 Запуск демо-напоминаний...")
    print(f"📅 Интервал: {interval_minutes} минут")
    if duration_hours:
        print(f"⏱️  Продолжительность: {duration_hours} часов")
    print("💬 Сообщения будут отправляться автоматически")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    demo_system = DemoReminderSystem()
    
    try:
        if duration_hours:
            # Запускаем на определенное время
            await asyncio.wait_for(
                demo_system.run_demo_loop(interval_minutes=interval_minutes),
                timeout=duration_hours * 3600
            )
        else:
            # Запускаем бесконечно
            await demo_system.run_demo_loop(interval_minutes=interval_minutes)
    except asyncio.TimeoutError:
        print(f"\n⏰ Демо-напоминания завершены (прошло {duration_hours} часов)")
    except KeyboardInterrupt:
        print("\n⏹️  Демо-напоминания остановлены пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Запуск демо-напоминаний")
    parser.add_argument(
        "--interval", 
        type=int, 
        default=15, 
        help="Интервал между сообщениями в минутах (по умолчанию: 15)"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        help="Продолжительность работы в часах (по умолчанию: бесконечно)"
    )
    
    args = parser.parse_args()
    
    # Проверяем аргументы
    if args.interval < 1:
        print("❌ Интервал должен быть не менее 1 минуты")
        return
    
    if args.duration and args.duration < 1:
        print("❌ Продолжительность должна быть не менее 1 часа")
        return
    
    # Запускаем демо
    asyncio.run(run_demo(args.interval, args.duration))

if __name__ == "__main__":
    main() 