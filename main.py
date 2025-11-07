#!/usr/bin/env python3
"""
Steam Avatar Auto-Changer
Автоматическая смена аватарок для Steam аккаунтов
"""
import sys
import os
import time
import logging
from colorama import init, Fore, Style

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from steam_manager import SteamManager
from account_manager import AccountManager, Account
from avatar_manager import AvatarManager

# Инициализация colorama для цветного вывода
init(autoreset=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_header():
    """Вывод заголовка программы"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  Steam Avatar Auto-Changer")
    print(f"{Fore.CYAN}  Автоматическая смена аватарок в Steam")
    print(f"{Fore.CYAN}{'='*60}\n")


def print_stats(accounts_count: int, avatars_count: int):
    """Вывод статистики"""
    print(f"{Fore.YELLOW}📊 Статистика:")
    print(f"   Загружено аккаунтов: {Fore.GREEN}{accounts_count}")
    print(f"   Загружено аватарок: {Fore.GREEN}{avatars_count}\n")


def main():
    """Главная функция программы"""
    print_header()

    # Создаем необходимые директории
    os.makedirs('logs', exist_ok=True)
    os.makedirs('accounts', exist_ok=True)
    os.makedirs('avatars', exist_ok=True)

    # Инициализация менеджеров
    steam_manager = SteamManager()
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
    print_stats(len(accounts), len(avatars))

    # Получаем уникальные аватарки для каждого аккаунта
    print(f"{Fore.CYAN}🎲 Выбор случайных аватарок для аккаунтов...\n")
    selected_avatars = avatar_manager.get_unique_avatars(len(accounts))

    # Обработка каждого аккаунта
    success_count = 0
    fail_count = 0

    for i, account in enumerate(accounts):
        print(f"{Fore.CYAN}{'─'*60}")
        print(f"{Fore.CYAN}[{i+1}/{len(accounts)}] Обработка аккаунта: {Fore.WHITE}{account.username}")

        # Авторизация
        print(f"{Fore.YELLOW}  🔐 Авторизация...")
        if not steam_manager.login(account.username, account.password, account.shared_secret):
            print(f"{Fore.RED}  ✗ Ошибка авторизации\n")
            fail_count += 1
            continue

        # Небольшая задержка после авторизации
        time.sleep(2)

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

        # Выход из аккаунта
        steam_manager.logout(account.username)

        # Задержка между аккаунтами
        if i < len(accounts) - 1:
            print(f"{Fore.YELLOW}  ⏳ Задержка 5 секунд...")
            time.sleep(5)

    # Итоговая статистика
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}📈 Итоговая статистика:")
    print(f"{Fore.GREEN}   ✓ Успешно: {success_count}")
    print(f"{Fore.RED}   ✗ Ошибок: {fail_count}")
    print(f"{Fore.CYAN}{'='*60}\n")

    # Выход из всех оставшихся сессий
    steam_manager.logout_all()

    print(f"{Fore.GREEN}✓ Программа завершена!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}✗ Критическая ошибка: {str(e)}")
        sys.exit(1)
