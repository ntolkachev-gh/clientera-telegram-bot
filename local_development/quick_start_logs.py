#!/usr/bin/env python3
"""
Быстрый запуск с просмотром логов Docker сервисов
"""

import subprocess
import sys
import signal
import threading
import time

def run_logs_with_color(service_name, color_code):
    """Запускает просмотр логов для сервиса с цветовой маркировкой"""
    try:
        process = subprocess.Popen(
            f"docker-compose logs -f {service_name}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Читаем логи в реальном времени
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                timestamp = time.strftime("%H:%M:%S")
                print(f"{color_code}[{timestamp}] {service_name.upper()}:{color_code[0]} {line.strip()}")

    except Exception as e:
        print(f"❌ Ошибка просмотра логов {service_name}: {e}")

def main():
    print("🚀 Быстрый запуск с просмотром логов")
    print("=" * 50)

    # Проверяем Docker
    try:
        subprocess.run("docker --version", shell=True, check=True, capture_output=True)
    except:
        print("❌ Docker не установлен или не запущен")
        print("💡 Установите Docker Desktop для macOS")
        return

    # Проверяем docker-compose
    try:
        subprocess.run("docker-compose --version", shell=True, check=True, capture_output=True)
    except:
        print("❌ Docker Compose не установлен")
        return

    # Запускаем сервисы
    print("🐳 Запуск Docker сервисов...")
    try:
        subprocess.run("docker-compose up -d", shell=True, check=True)
        print("✅ Сервисы запущены")
    except:
        print("❌ Ошибка запуска сервисов")
        return

    # Ждем готовности PostgreSQL
    print("⏳ Ожидание готовности PostgreSQL...")
    for i in range(15):
        try:
            result = subprocess.run(
                "docker-compose exec -T postgres pg_isready -U bot_user -d bot_db",
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ PostgreSQL готов!")
                break
        except:
            pass
        time.sleep(2)

    print("\n📊 Запуск просмотра логов...")
    print("💡 Нажмите Ctrl+C для остановки")
    print("=" * 50)

    # Запускаем просмотр логов в отдельных потоках
    threads = []

    # PostgreSQL логи (желтый)
    postgres_thread = threading.Thread(
        target=run_logs_with_color,
        args=("postgres", "\033[33m")
    )
    postgres_thread.daemon = True
    postgres_thread.start()
    threads.append(postgres_thread)

    # Qdrant логи (пурпурный)
    qdrant_thread = threading.Thread(
        target=run_logs_with_color,
        args=("qdrant", "\033[35m")
    )
    qdrant_thread.daemon = True
    qdrant_thread.start()
    threads.append(qdrant_thread)

    # PgAdmin логи (синий)
    pgadmin_thread = threading.Thread(
        target=run_logs_with_color,
        args=("pgadmin", "\033[34m")
    )
    pgadmin_thread.daemon = True
    pgadmin_thread.start()
    threads.append(pgadmin_thread)

    try:
        # Ждем завершения
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка...")
        subprocess.run("docker-compose down", shell=True)
        print("👋 Сервисы остановлены")

if __name__ == "__main__":
    main()
