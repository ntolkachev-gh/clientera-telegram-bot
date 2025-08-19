#!/usr/bin/env python3
"""
Скрипт запуска simple_main.py бота
"""

import sys
import os

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.simple_main import main
import asyncio

if __name__ == "__main__":
    print("🚀 Запуск простого Telegram бота...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        raise
