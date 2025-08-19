#!/usr/bin/env python3
"""
Скрипт для очистки занятых портов
"""

import subprocess
import sys

def clear_port(port):
    """Очищает указанный порт, убивая процесс на нем"""
    try:
        # Находим PID процесса на порту
        result = subprocess.run(
            f"lsof -ti:{port}",
            shell=True, capture_output=True, text=True
        )

        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🔍 Найдены процессы на порту {port}: {pids}")

            for pid in pids:
                if pid:
                    try:
                        subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                        print(f"✅ Процесс {pid} убит")
                    except subprocess.CalledProcessError:
                        print(f"❌ Не удалось убить процесс {pid}")

            # Проверяем, что порт освобожден
            time.sleep(1)
            result = subprocess.run(
                f"lsof -ti:{port}",
                shell=True, capture_output=True, text=True
            )

            if not result.stdout.strip():
                print(f"✅ Порт {port} освобожден")
                return True
            else:
                print(f"⚠️ Порт {port} все еще занят")
                return False
        else:
            print(f"✅ Порт {port} уже свободен")
            return True

    except Exception as e:
        print(f"❌ Ошибка при очистке порта {port}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Использование: python3 clear_ports.py <порт1> [порт2] [порт3] ...")
        print("Пример: python3 clear_ports.py 8081 5000 3000")
        return

    ports = [int(port) for port in sys.argv[1:]]

    print("🧹 Очистка портов...")
    print("=" * 40)

    for port in ports:
        print(f"\n🔍 Очистка порта {port}...")
        clear_port(port)

    print("\n" + "=" * 40)
    print("🎉 Очистка завершена!")

if __name__ == "__main__":
    import time
    main()
