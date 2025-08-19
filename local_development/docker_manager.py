#!/usr/bin/env python3
"""
Скрипт для управления Docker контейнерами
"""

import subprocess
import sys
import time
import os

def run_command(command, check=True):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_docker():
    """Проверяет, установлен ли Docker"""
    print("🔍 Проверка Docker...")

    success, stdout, stderr = run_command("docker --version", check=False)
    if success:
        print(f"✅ Docker установлен: {stdout.strip()}")
        return True
    else:
        print("❌ Docker не установлен или не запущен")
        print("💡 Установите Docker Desktop для macOS")
        return False

def check_docker_compose():
    """Проверяет, установлен ли Docker Compose"""
    print("🔍 Проверка Docker Compose...")

    success, stdout, stderr = run_command("docker-compose --version", check=False)
    if success:
        print(f"✅ Docker Compose установлен: {stdout.strip()}")
        return True
    else:
        print("❌ Docker Compose не установлен")
        print("💡 Docker Compose обычно идет в комплекте с Docker Desktop")
        return False

def start_services():
    """Запускает сервисы"""
    print("🚀 Запуск сервисов...")

    if not os.path.exists('docker-compose.yml'):
        print("❌ Файл docker-compose.yml не найден")
        return False

    success, stdout, stderr = run_command("docker-compose up -d")
    if success:
        print("✅ Сервисы запущены успешно!")
        print("📊 Статус сервисов:")
        run_command("docker-compose ps")
        return True
    else:
        print(f"❌ Ошибка запуска сервисов: {stderr}")
        return False

def stop_services():
    """Останавливает сервисы"""
    print("🛑 Остановка сервисов...")

    success, stdout, stderr = run_command("docker-compose down")
    if success:
        print("✅ Сервисы остановлены")
        return True
    else:
        print(f"❌ Ошибка остановки сервисов: {stderr}")
        return False

def restart_services():
    """Перезапускает сервисы"""
    print("🔄 Перезапуск сервисов...")

    stop_services()
    time.sleep(2)
    return start_services()

def show_status():
    """Показывает статус сервисов"""
    print("📊 Статус сервисов:")
    run_command("docker-compose ps")

    print("\n📊 Логи PostgreSQL:")
    run_command("docker-compose logs --tail=10 postgres")

    print("\n📊 Логи PgAdmin:")
    run_command("docker-compose logs --tail=5 pgadmin")

def show_logs():
    """Показывает логи сервисов"""
    print("📋 Логи сервисов:")
    print("\n" + "="*50)

    print("🗄️ PostgreSQL логи:")
    run_command("docker-compose logs postgres")

    print("\n" + "="*50)
    print("🖥️ PgAdmin логи:")
    run_command("docker-compose logs pgadmin")

def wait_for_postgres():
    """Ждет, пока PostgreSQL будет готов"""
    print("⏳ Ожидание готовности PostgreSQL...")

    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        success, stdout, stderr = run_command(
            "docker-compose exec -T postgres pg_isready -U bot_user -d bot_db",
            check=False
        )

        if success:
            print("✅ PostgreSQL готов к работе!")
            return True

        attempt += 1
        print(f"⏳ Попытка {attempt}/{max_attempts}...")
        time.sleep(2)

    print("❌ PostgreSQL не готов после 30 попыток")
    return False

def update_env_file():
    """Обновляет .env файл с данными для Docker"""
    print("🔧 Обновление .env файла для Docker...")

    docker_db_url = "postgresql://bot_user:bot_password@localhost:5432/bot_db"

    # Читаем существующий .env файл
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()

    # Обновляем или добавляем DATABASE_URL
    if 'DATABASE_URL=' in env_content:
        # Заменяем существующую строку
        lines = env_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('DATABASE_URL='):
                lines[i] = f'DATABASE_URL={docker_db_url}'
                break
        env_content = '\n'.join(lines)
    else:
        # Добавляем новую строку
        env_content += f'\nDATABASE_URL={docker_db_url}\n'

    # Записываем обновленный файл
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)

    print(f"✅ DATABASE_URL обновлен: {docker_db_url}")
    return True

def show_help():
    """Показывает справку"""
    print("""
🚀 Docker Manager для бота

Использование:
  python3 docker_manager.py [команда]

Команды:
  start     - Запустить сервисы
  stop      - Остановить сервисы
  restart   - Перезапустить сервисы
  status    - Показать статус
  logs      - Показать логи
  wait      - Ждать готовности PostgreSQL
  update    - Обновить .env файл
  help      - Показать эту справку

Примеры:
  python3 docker_manager.py start
  python3 docker_manager.py status
  python3 docker_manager.py logs

💡 После запуска сервисов:
  - PostgreSQL будет доступен на localhost:5432
  - PgAdmin будет доступен на http://localhost:8080
  - Логин: admin@bot.local / admin
    """)

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    # Проверяем Docker
    if not check_docker():
        return

    if not check_docker_compose():
        return

    # Выполняем команду
    if command == 'start':
        if start_services():
            update_env_file()
            print("\n🎉 Сервисы запущены!")
            print("📊 PostgreSQL: localhost:5432")
            print("🖥️ PgAdmin: http://localhost:8080")
            print("💡 Логин PgAdmin: admin@bot.local / admin")

            print("\n⏳ Ожидание готовности PostgreSQL...")
            if wait_for_postgres():
                print("\n✅ Теперь можно запускать бота!")
                print("🚀 python3 local_test.py")

    elif command == 'stop':
        stop_services()

    elif command == 'restart':
        restart_services()

    elif command == 'status':
        show_status()

    elif command == 'logs':
        show_logs()

    elif command == 'wait':
        wait_for_postgres()

    elif command == 'update':
        update_env_file()

    elif command == 'help':
        show_help()

    else:
        print(f"❌ Неизвестная команда: {command}")
        show_help()

if __name__ == "__main__":
    main()

