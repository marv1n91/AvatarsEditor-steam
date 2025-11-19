#!/usr/bin/env python3
"""
Steam Points Gift Manager
Автоматическое дарение подарков Steam Points с нескольких аккаунтов
"""
import sys
import os
import asyncio
import logging
import argparse
from datetime import datetime
from colorama import init, Fore, Style

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from steam_points_manager import SteamPointsManager, process_accounts_batch
from account_manager import AccountManager

# Инициализация colorama для цветного вывода
init(autoreset=True)

logger = logging.getLogger(__name__)


def print_header():
    """Вывод заголовка программы"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}  Steam Points Gift Manager")
    print(f"{Fore.CYAN}  Автоматическое дарение подарков Steam Points")
    print(f"{Fore.CYAN}{'='*70}\n")


def print_stats(results: list):
    """
    Вывод статистики результатов

    Args:
        results: Список результатов обработки аккаунтов
    """
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful

    total_points = sum(r.get('points_balance', 0) for r in results)
    total_gifts_cost = sum(
        r.get('gift_sent', {}).get('cost', 0)
        for r in results if r['success']
    )

    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📈 Итоговая статистика:")
    print(f"{Fore.GREEN}   ✓ Успешно обработано: {successful}/{total}")
    print(f"{Fore.RED}   ✗ Ошибок: {failed}/{total}")
    print(f"{Fore.YELLOW}   💰 Всего очков найдено: {total_points:,}")
    print(f"{Fore.YELLOW}   🎁 Стоимость отправленных подарков: {total_gifts_cost:,}")

    if total > 0:
        success_rate = (successful / total) * 100
        print(f"{Fore.CYAN}   📊 Процент успеха: {Fore.WHITE}{success_rate:.1f}%")

    print(f"{Fore.CYAN}{'='*70}\n")


def print_account_result(result: dict, index: int, total: int):
    """
    Вывод результата обработки одного аккаунта

    Args:
        result: Результат обработки
        index: Номер аккаунта
        total: Общее количество аккаунтов
    """
    username = result['username']
    print(f"{Fore.CYAN}{'─'*70}")
    print(f"{Fore.CYAN}[{index}/{total}] Аккаунт: {Fore.WHITE}{username}")

    if result['success']:
        points = result.get('points_balance', 0)
        gift = result.get('gift_sent', {})
        gift_name = gift.get('name', 'Unknown')
        gift_cost = gift.get('cost', 0)

        print(f"{Fore.GREEN}  ✓ Успешно обработан")
        print(f"{Fore.YELLOW}  💰 Баланс очков: {points:,}")
        print(f"{Fore.YELLOW}  🎁 Отправлен подарок: {gift_name} ({gift_cost:,} очков)")
    else:
        error = result.get('error', 'Неизвестная ошибка')
        points = result.get('points_balance', 0)

        print(f"{Fore.RED}  ✗ Ошибка: {error}")
        if points > 0:
            print(f"{Fore.YELLOW}  💰 Баланс очков: {points:,}")


async def get_recipient_steamid(manager: SteamPointsManager, username: str,
                                password: str, shared_secret: str) -> str:
    """
    Получение Steam ID аккаунта-получателя

    Args:
        manager: SteamPointsManager instance
        username: Логин
        password: Пароль
        shared_secret: Shared secret

    Returns:
        Steam ID или пустая строка
    """
    try:
        auth_data = await manager.login(username, password, shared_secret)
        if auth_data:
            steamid = auth_data.get('steamid')
            if steamid:
                logger.info(f"✓ Steam ID получателя: {steamid}")
                return steamid
    except Exception as e:
        logger.error(f"Ошибка получения Steam ID: {str(e)}")

    return ""


def setup_logging(verbose: bool = False):
    """Настройка логирования"""
    level = logging.DEBUG if verbose else logging.INFO

    # Создаем директорию для логов
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/steam_gifts.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


async def main_async(args):
    """Асинхронная главная функция"""
    print_header()

    # Загрузка аккаунтов
    print(f"{Fore.CYAN}🔄 Загрузка аккаунтов...")
    account_manager = AccountManager(args.accounts_file)
    accounts = account_manager.load_accounts()

    if not accounts:
        print(f"{Fore.RED}✗ Не найдено аккаунтов!")
        print(f"{Fore.YELLOW}💡 Добавьте аккаунты в файл {args.accounts_file}")
        print(f"{Fore.YELLOW}   Формат: username:password:shared_secret")
        return 1

    print(f"{Fore.GREEN}✓ Загружено аккаунтов: {len(accounts)}\n")

    # Получение Steam ID получателя
    recipient_steamid = args.recipient_steamid

    if not recipient_steamid:
        # Если не указан Steam ID, пытаемся получить его из логина получателя
        if args.recipient_login:
            print(f"{Fore.CYAN}🔍 Получение Steam ID для {args.recipient_login}...")

            # Ищем аккаунт получателя в списке
            recipient_account = None
            for acc in accounts:
                if acc.username == args.recipient_login:
                    recipient_account = acc
                    break

            if recipient_account:
                async with SteamPointsManager() as manager:
                    recipient_steamid = await get_recipient_steamid(
                        manager,
                        recipient_account.username,
                        recipient_account.password,
                        recipient_account.shared_secret
                    )

                if not recipient_steamid:
                    print(f"{Fore.RED}✗ Не удалось получить Steam ID получателя")
                    return 1
            else:
                print(f"{Fore.RED}✗ Аккаунт получателя '{args.recipient_login}' не найден в списке")
                return 1
        else:
            print(f"{Fore.RED}✗ Необходимо указать --recipient-steamid или --recipient-login")
            return 1

    print(f"{Fore.GREEN}✓ Steam ID получателя: {recipient_steamid}\n")

    # Подготовка данных аккаунтов
    account_data = [
        (acc.username, acc.password, acc.shared_secret)
        for acc in accounts
        if acc.username != args.recipient_login  # Исключаем аккаунт получателя
    ]

    if not account_data:
        print(f"{Fore.RED}✗ Нет аккаунтов для обработки после исключения получателя")
        return 1

    print(f"{Fore.CYAN}📊 Аккаунтов для обработки: {len(account_data)}")
    print(f"{Fore.CYAN}⚙️  Максимум одновременных операций: {args.max_concurrent}\n")
    print(f"{Fore.CYAN}⏱️  Начало обработки: {datetime.now().strftime('%H:%M:%S')}\n")

    # Обработка аккаунтов
    try:
        results = await process_accounts_batch(
            account_data,
            recipient_steamid,
            max_concurrent=args.max_concurrent
        )

        # Вывод результатов
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}📋 Результаты обработки:")
        print(f"{Fore.CYAN}{'='*70}\n")

        for i, result in enumerate(results, 1):
            print_account_result(result, i, len(results))

        # Вывод итоговой статистики
        print_stats(results)

        # Сохранение результатов в файл
        if args.save_results:
            import json
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f'logs/results_{timestamp}.json'

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"{Fore.GREEN}✓ Результаты сохранены в {results_file}\n")

        print(f"{Fore.GREEN}✓ Обработка завершена!")
        return 0

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Обработка прервана пользователем")
        return 130
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}✗ Критическая ошибка: {str(e)}")
        return 1


def main():
    """Главная функция программы"""
    parser = argparse.ArgumentParser(
        description='Steam Points Gift Manager - автоматическое дарение подарков',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Отправить подарки на указанный Steam ID
  python steam_gifts.py --recipient-steamid 76561198012345678

  # Отправить подарки на аккаунт из списка
  python steam_gifts.py --recipient-login targetuser

  # Указать файл с аккаунтами и количество потоков
  python steam_gifts.py --recipient-login targetuser --accounts accounts/accounts.txt --max-concurrent 10

  # Включить подробное логирование и сохранить результаты
  python steam_gifts.py --recipient-steamid 76561198012345678 --verbose --save-results
        """
    )

    parser.add_argument(
        '--accounts-file',
        type=str,
        default='accounts/accounts.txt',
        help='Путь к файлу с аккаунтами (по умолчанию: accounts/accounts.txt)'
    )

    parser.add_argument(
        '--recipient-steamid',
        type=str,
        help='Steam ID получателя подарков'
    )

    parser.add_argument(
        '--recipient-login',
        type=str,
        help='Логин получателя подарков (из списка аккаунтов)'
    )

    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Максимальное количество одновременных операций (по умолчанию: 5)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Подробное логирование'
    )

    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Сохранить результаты в JSON файл'
    )

    args = parser.parse_args()

    # Настройка логирования
    setup_logging(args.verbose)

    # Запуск асинхронной обработки
    try:
        if sys.platform == 'win32':
            # Windows требует особой настройки event loop
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}✗ Критическая ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
