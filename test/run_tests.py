"""
Скрипт для запуска тестов
"""
import subprocess
import sys
import os
import argparse

def run_tests(test_path=None, verbose=True, show_coverage=False):
    """
    Запуск тестов

    Args:
        test_path: Путь к конкретному тесту или директории (по умолчанию test/)
        verbose: Подробный вывод
        show_coverage: Показать покрытие кода
    """
    # Переходим в корневую директорию проекта
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.chdir(project_root)

    # Устанавливаем тестовые зависимости
    print("📦 Устанавливаем тестовые зависимости...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "test/requirements.txt"], check=True)

    # Формируем команду для запуска тестов
    test_target = test_path if test_path else "test/"

    cmd = [
        sys.executable, "-m", "pytest",
        test_target,
        "--tb=short",
        "--color=yes"
    ]

    if verbose:
        cmd.append("-v")

    if show_coverage:
        cmd.extend(["--cov=core", "--cov-report=term-missing"])

    # Запускаем тесты
    print(f"🧪 Запускаем тесты: {test_target}")
    result = subprocess.run(cmd)

    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Запуск тестов для OpenAI Tools")
    parser.add_argument("test", nargs="?", help="Путь к конкретному тесту или модулю")
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")
    parser.add_argument("-q", "--quiet", action="store_true", help="Минимальный вывод")
    parser.add_argument("--coverage", action="store_true", help="Показать покрытие кода")
    parser.add_argument("--services", action="store_true", help="Запустить только тесты сервисов")
    parser.add_argument("--staff", action="store_true", help="Запустить только тесты мастеров")

    args = parser.parse_args()

    # Определяем что запускать
    test_path = args.test

    if args.services:
        test_path = "test/test_find_service_by_name.py"
        print("🔍 Запуск тестов для сервисов...")
    elif args.staff:
        test_path = "test/test_get_staff.py test/test_find_staff_by_name.py"
        print("👥 Запуск тестов для мастеров...")

    verbose = args.verbose and not args.quiet

    exit_code = run_tests(test_path, verbose, args.coverage)

    # Выводим итоговую статистику
    if exit_code == 0:
        print("\n✅ Все тесты прошли успешно!")
    else:
        print(f"\n❌ Тесты завершились с ошибкой (код: {exit_code})")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
