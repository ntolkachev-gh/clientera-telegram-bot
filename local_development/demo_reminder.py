#!/usr/bin/env python3
"""
Скрипт для запуска демо-напоминаний
Запускает отправку приглашений каждые 15 минут
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.demo_reminder import DemoReminderSystem

async def main():
    """Запуск демо-напоминаний"""
    print("🚀 Запуск демо-напоминаний...")
    print("📅 Интервал: 15 минут")
    print("💬 Сообщения будут отправляться автоматически")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    demo_system = DemoReminderSystem()
    
    try:
        await demo_system.run_demo_loop(interval_minutes=15)
    except KeyboardInterrupt:
        print("\n⏹️  Демо-напоминания остановлены")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 