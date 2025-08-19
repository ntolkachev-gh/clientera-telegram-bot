#!/usr/bin/env python3
"""
Скрипт для запуска local_bot_web.py с логами в реальном времени
"""

import subprocess
import sys
import time
import os
import signal
import threading
import socket
from pathlib import Path

class LocalWebRunner:
    def __init__(self):
        self.processes = []
        self.running = True
        self.web_port = 8081

    def find_free_port(self, start_port=8081):
        """Находит свободный порт начиная с start_port"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return None

    def kill_process_on_port(self, port):
        """Убивает процесс, использующий указанный порт"""
        try:
            result = subprocess.run(
                f"lsof -ti:{port}",
                shell=True, capture_output=True, text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(f"kill -9 {pid}", shell=True)
                        print(f"🛑 Убит процесс {pid} на порту {port}")
                        time.sleep(1)  # Даем время на освобождение порта
                return True
        except:
            pass
        return False

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
                    # Используем цветовую схему для разных сервисов
                    reset_color = "\033[0m"
                    print(f"{color_code}[{timestamp}] {name}:{reset_color} {line.strip()}", flush=True)

        except Exception as e:
            print(f"❌ Ошибка запуска {name}: {e}", flush=True)

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

    def start_local_web_bot(self):
        """Запускает локальный веб-бот"""
        print("🤖 Запуск локального веб-бота...")

        # Находим свободный порт
        self.web_port = self.find_free_port(8081)
        if not self.web_port:
            print("❌ Не удалось найти свободный порт")
            return False

        print(f"🔍 Найден свободный порт: {self.web_port}")

        # Если порт 8081 занят, пытаемся освободить его
        if self.web_port != 8081:
            print(f"⚠️ Порт 8081 занят, используем {self.web_port}")
            if self.kill_process_on_port(8081):
                # Пробуем снова найти свободный порт
                self.web_port = self.find_free_port(8081)
                if self.web_port == 8081:
                    print("✅ Порт 8081 освобожден, используем его")

        # Запускаем бота напрямую (блокирующий вызов)
        print(f"✅ Запускаем локальный веб-бот на http://localhost:{self.web_port}")
        self.run_web_bot_with_direct_logs(self.web_port)
        return True

    def run_web_bot_with_direct_logs(self, port):
        """Запускает веб-бот с прямым выводом логов"""
        try:
            # Устанавливаем переменные окружения для правильного логирования
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Отключаем буферизацию вывода
            env['FLASK_ENV'] = 'development'

            process = subprocess.Popen(
                f"python3 local_bot_web.py --port {port}",
                shell=True,
                stdout=sys.stdout,  # Прямой вывод в консоль
                stderr=sys.stderr,  # Прямой вывод ошибок в консоль
                env=env
            )

            self.processes.append((process, "WEB_BOT"))
            process.wait()  # Ждем завершения процесса

        except Exception as e:
            print(f"❌ Ошибка запуска веб-бота: {e}", flush=True)

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
        print("🚀 Запуск local_bot_web.py с логами в реальном времени")
        print("=" * 60)

        # Регистрируем обработчик сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            # Запускаем Docker сервисы
            if not self.start_docker_services():
                return

            # Запускаем мониторинг логов Docker в фоне
            self.start_log_monitoring()

            # Небольшая пауза для инициализации
            time.sleep(3)

            print("\n" + "=" * 60)
            print("🎉 Все сервисы готовы! Запускаем веб-бот...")
            print("🗄️ PostgreSQL: localhost:5432")
            print("🔍 Qdrant: localhost:6333")
            print("🖥️ PgAdmin: http://localhost:8080 (admin/admin)")
            print("=" * 60)
            print("💡 Логи веб-бота будут показаны ниже:")
            print("💡 Нажмите Ctrl+C для остановки всех сервисов")
            print("=" * 60)

            # Запускаем локальный веб-бот (это блокирующий вызов)
            # Веб-бот будет работать до получения сигнала завершения
            self.start_local_web_bot()

        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал завершения...")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            self.stop_all()
            print("👋 Приложение остановлено")

def main():
    """Точка входа"""
    runner = LocalWebRunner()
    runner.run()

if __name__ == "__main__":
    main()
