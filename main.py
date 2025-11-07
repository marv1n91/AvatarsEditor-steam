#!/usr/bin/env python3
"""
Steam Avatar Auto-Changer
Автоматическая смена аватарок для Steam аккаунтов
"""
import sys
import os
import time
import logging
import configparser
import argparse
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from steam_manager import SteamManager
from account_manager import AccountManager, Account
from avatar_manager import AvatarManager

# Инициализация colorama для цветного вывода
init(autoreset=True)

# Глобальная переменная для логгера (настраивается позже)
logger = None


def print_header():
    """Вывод заголовка программы"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  Steam Avatar Auto-Changer")
    print(f"{Fore.CYAN}  Автоматическая смена аватарок в Steam")
    print(f"{Fore.CYAN}{'='*60}\n")


def print_stats(accounts_count: int, avatars_count: int, delay: int):
    """Вывод статистики"""
    print(f"{Fore.YELLOW}📊 Статистика:")
    print(f"   Загружено аккаунтов: {Fore.GREEN}{accounts_count}")
    print(f"   Загружено аватарок: {Fore.GREEN}{avatars_count}")
    print(f"   Задержка между аккаунтами: {Fore.GREEN}{delay} сек ({delay//60} мин {delay%60} сек)\n")


def load_config(config_file: str = 'config.ini'):
    """Загрузка конфигурации"""
    config = configparser.ConfigParser()

    # Значения по умолчанию
    default_config = {
        'delay_between_accounts': 60,
        'delay_after_login': 2,
        'show_countdown': True,
        'log_level': 'INFO'
    }

    if os.path.exists(config_file):
        config.read(config_file, encoding='utf-8')

        delay_between = config.getint('Settings', 'delay_between_accounts', fallback=60)
        delay_after = config.getint('Settings', 'delay_after_login', fallback=2)
        show_countdown = config.getboolean('Settings', 'show_countdown', fallback=True)
        log_level = config.get('Settings', 'log_level', fallback='INFO')

        return {
            'delay_between_accounts': delay_between,
            'delay_after_login': delay_after,
            'show_countdown': show_countdown,
            'log_level': log_level
        }
    else:
        if logger:
            logger.warning(f"Файл конфигурации {config_file} не найден. Используются значения по умолчанию.")
        return default_config


def countdown_timer(seconds: int, message: str = "Ожидание"):
    """
    Таймер обратного отсчета с визуализацией

    Args:
        seconds: Количество секунд для ожидания
        message: Сообщение для отображения
    """
    end_time = datetime.now() + timedelta(seconds=seconds)

    while True:
        remaining = (end_time - datetime.now()).total_seconds()

        if remaining <= 0:
            break

        mins, secs = divmod(int(remaining), 60)
        timer = f"{mins:02d}:{secs:02d}"

        # Прогресс бар
        progress = int((seconds - remaining) / seconds * 30)
        bar = '█' * progress + '░' * (30 - progress)

        print(f"\r{Fore.YELLOW}  ⏳ {message}: [{bar}] {timer}", end='', flush=True)
        time.sleep(0.5)

    print(f"\r{Fore.GREEN}  ✓ Ожидание завершено!{' ' * 50}")


def setup_logging(log_level: str):
    """Настройка логирования"""
    global logger

    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)


def main():
    """Главная функция программы"""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Steam Avatar Auto-Changer')
    parser.add_argument('-d', '--delay', type=int, help='Задержка между аккаунтами (секунды)')
    parser.add_argument('-c', '--config', type=str, default='config.ini', help='Путь к файлу конфигурации')
    parser.add_argument('--no-countdown', action='store_true', help='Отключить таймер обратного отсчета')
    args = parser.parse_args()

    print_header()

    # Создаем необходимые директории
    os.makedirs('logs', exist_ok=True)
    os.makedirs('accounts', exist_ok=True)
    os.makedirs('avatars', exist_ok=True)

    # Временная настройка логирования для загрузки конфига
    setup_logging('INFO')

    # Загрузка конфигурации
    config = load_config(args.config)

    # Настройка логирования с уровнем из конфига
    setup_logging(config['log_level'])

    # Переопределение задержки из аргументов командной строки
    if args.delay is not None:
        config['delay_between_accounts'] = args.delay

    if args.no_countdown:
        config['show_countdown'] = False

    # Инициализация менеджеров
    account_manager = AccountManager('accounts/accounts.txt')
    avatar_manager = AvatarManager('avatars')

    # Загрузка аккаунтов
    print(f"{Fore.CYAN}🔄 Загрузка аккаунтов...")
    accounts = account_manager.load_accounts()

    if not accounts:
        print(f"{Fore.RED}✗ Не найдено аккаунтов!")
        print(f"{Fore.YELLOW}💡 Добавьте аккаунты в файл accounts/accounts.txt")
        print(f"{Fore.YELLOW}   Формат: username:password или username:password:shared_secret")
        return

    # Загрузка аватарок
    print(f"{Fore.CYAN}🔄 Загрузка аватарок...")
    avatars = avatar_manager.load_avatars()

    if not avatars:
        print(f"{Fore.RED}✗ Не найдено аватарок!")
        print(f"{Fore.YELLOW}💡 Добавьте изображения в папку avatars/")
        print(f"{Fore.YELLOW}   Поддерживаемые форматы: JPG, PNG, GIF, BMP")
        return

    # Вывод статистики
    print_stats(len(accounts), len(avatars), config['delay_between_accounts'])

    # Получаем уникальные аватарки для каждого аккаунта
    print(f"{Fore.CYAN}🎲 Выбор случайных аватарок для аккаунтов...\n")
    selected_avatars = avatar_manager.get_unique_avatars(len(accounts))

    # Расчет общего времени выполнения
    total_time = (len(accounts) - 1) * config['delay_between_accounts']
    hours, remainder = divmod(total_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"{Fore.CYAN}⏱️  Примерное время выполнения: ", end='')
    if hours > 0:
        print(f"{Fore.WHITE}{hours}ч {minutes}мин")
    elif minutes > 0:
        print(f"{Fore.WHITE}{minutes}мин {seconds}сек")
    else:
        print(f"{Fore.WHITE}{seconds}сек")

    finish_time = datetime.now() + timedelta(seconds=total_time)
    print(f"{Fore.CYAN}🎯 Ожидаемое время завершения: {Fore.WHITE}{finish_time.strftime('%H:%M:%S')}\n")

    # Обработка каждого аккаунта
    success_count = 0
    fail_count = 0

    for i, account in enumerate(accounts):
        print(f"{Fore.CYAN}{'─'*60}")
        print(f"{Fore.CYAN}[{i+1}/{len(accounts)}] Обработка аккаунта: {Fore.WHITE}{account.username}")

        # Создаем новый экземпляр браузера для каждого аккаунта
        steam_manager = SteamManager()

        try:
            # Авторизация
            print(f"{Fore.YELLOW}  🔐 Авторизация...")
            if not steam_manager.login(account.username, account.password, account.shared_secret):
                print(f"{Fore.RED}  ✗ Ошибка авторизации\n")
                fail_count += 1
                continue

            # Задержка после авторизации
            time.sleep(config['delay_after_login'])

            # Смена аватарки
            avatar_path = selected_avatars[i]
            avatar_name = os.path.basename(avatar_path)
            print(f"{Fore.YELLOW}  🖼️  Установка аватарки: {avatar_name}")

            if steam_manager.change_avatar(account.username, avatar_path):
                print(f"{Fore.GREEN}  ✓ Аватарка успешно изменена!")
                success_count += 1
            else:
                print(f"{Fore.RED}  ✗ Не удалось изменить аватарку")
                fail_count += 1

        finally:
            # Полностью закрываем браузер после каждого аккаунта
            steam_manager.logout_all()

        # Задержка между аккаунтами
        if i < len(accounts) - 1:
            delay = config['delay_between_accounts']

            if config['show_countdown'] and delay > 10:
                countdown_timer(delay, f"До следующего аккаунта ({i+2}/{len(accounts)})")
            else:
                mins, secs = divmod(delay, 60)
                print(f"{Fore.YELLOW}  ⏳ Задержка {mins}:{secs:02d}...")
                time.sleep(delay)

            print()  # Пустая строка для разделения

    # Итоговая статистика
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}📈 Итоговая статистика:")
    print(f"{Fore.GREEN}   ✓ Успешно: {success_count}")
    print(f"{Fore.RED}   ✗ Ошибок: {fail_count}")
    print(f"{Fore.CYAN}   📊 Процент успеха: {Fore.WHITE}{(success_count / len(accounts) * 100):.1f}%")
    print(f"{Fore.CYAN}{'='*60}\n")

    print(f"{Fore.GREEN}✓ Программа завершена!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        if logger:
            logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}✗ Критическая ошибка: {str(e)}")
        sys.exit(1)
