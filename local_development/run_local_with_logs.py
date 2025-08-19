#!/usr/bin/env python3
"""
Скрипт для запуска приложения локально с просмотром логов в реальном времени
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

class LocalRunner:
    def __init__(self):
        self.processes = []
        self.running = True

    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print("\n🛑 Получен сигнал завершения, останавливаю процессы...")
        self.running = False
        self.stop_all()
        sys.exit(0)

    def run_command_with_logs(self, command, name, color_code="\033[94m"):
        """Запускает команду и выводит логи в реальном времени"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            self.processes.append((process, name))

            # Читаем вывод в реальном времени
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                if line.strip():
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"{color_code}[{timestamp}] {name}:{color_code[0]} {line.strip()}")

        except Exception as e:
            print(f"❌ Ошибка запуска {name}: {e}")

    def start_docker_services(self):
        """Запускает Docker сервисы"""
        print("🐳 Запуск Docker сервисов...")

        # Проверяем, что docker-compose.yml существует
        if not os.path.exists('docker-compose.yml'):
            print("❌ Файл docker-compose.yml не найден")
            return False

        # Запускаем сервисы в фоне
        subprocess.run("docker-compose up -d", shell=True, check=True)
        print("✅ Docker сервисы запущены")

        # Ждем готовности PostgreSQL
        print("⏳ Ожидание готовности PostgreSQL...")
        for i in range(30):
            try:
                result = subprocess.run(
                    "docker-compose exec -T postgres pg_isready -U bot_user -d bot_db",
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    print("✅ PostgreSQL готов к работе!")
                    break
            except:
                pass
            time.sleep(2)
            print(f"⏳ Попытка {i+1}/30...")
        else:
            print("⚠️ PostgreSQL не готов, но продолжаем...")

        return True

    def start_local_bot(self):
        """Запускает локальный бот"""
        print("🤖 Запуск локального бота...")

        # Запускаем бота в отдельном потоке
        bot_thread = threading.Thread(
            target=self.run_command_with_logs,
            args=("python3 local_test.py", "BOT", "\033[92m")
        )
        bot_thread.daemon = True
        bot_thread.start()

        print("✅ Локальный бот запущен на http://localhost:5000")

    def start_log_monitoring(self):
        """Запускает мониторинг логов Docker сервисов"""
        print("📊 Запуск мониторинга логов...")

        # Мониторинг PostgreSQL
        postgres_thread = threading.Thread(
            target=self.run_command_with_logs,
            args=("docker-compose logs -f postgres", "POSTGRES", "\033[33m")
        )
        postgres_thread.daemon = True
        postgres_thread.start()

        # Мониторинг Qdrant
        qdrant_thread = threading.Thread(
            target=self.run_command_with_logs,
            args=("docker-compose logs -f qdrant", "QDRANT", "\033[35m")
        )
        qdrant_thread.daemon = True
        qdrant_thread.start()

        print("✅ Мониторинг логов запущен")

    def stop_all(self):
        """Останавливает все процессы"""
        print("🛑 Остановка всех процессов...")

        # Останавливаем Docker сервисы
        try:
            subprocess.run("docker-compose down", shell=True)
            print("✅ Docker сервисы остановлены")
        except:
            pass

        # Завершаем процессы
        for process, name in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} остановлен")
            except:
                try:
                    process.kill()
                    print(f"✅ {name} принудительно остановлен")
                except:
                    pass

    def run(self):
        """Основной метод запуска"""
        print("🚀 Запуск приложения локально с логами в реальном времени")
        print("=" * 60)

        # Регистрируем обработчик сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            # Запускаем Docker сервисы
            if not self.start_docker_services():
                return

            # Запускаем мониторинг логов
            self.start_log_monitoring()

            # Небольшая пауза для инициализации
            time.sleep(3)

            # Запускаем локальный бот
            self.start_local_bot()

            print("\n" + "=" * 60)
            print("🎉 Приложение запущено!")
            print("📱 Веб-интерфейс: http://localhost:5000")
            print("🗄️ PostgreSQL: localhost:5432")
            print("🔍 Qdrant: localhost:6333")
            print("🖥️ PgAdmin: http://localhost:8080 (admin/admin)")
            print("=" * 60)
            print("💡 Нажмите Ctrl+C для остановки")
            print("=" * 60)

            # Ждем завершения
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал завершения...")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            self.stop_all()
            print("👋 Приложение остановлено")

def main():
    """Точка входа"""
    runner = LocalRunner()
    runner.run()

if __name__ == "__main__":
    main()
