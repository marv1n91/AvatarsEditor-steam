#!/usr/bin/env python3
"""
Тестовый скрипт для диагностики авторизации Steam
Запустите: python test_login.py
"""
import sys
import os
sys.path.insert(0, 'src')

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from steam_manager import SteamManager
from account_manager import AccountManager
import time

print("="*60)
print("ДИАГНОСТИКА АВТОРИЗАЦИИ STEAM")
print("="*60)
print()

# Загружаем аккаунты
print("1. Загрузка аккаунтов...")
account_manager = AccountManager('accounts/accounts.txt')
accounts = account_manager.load_accounts()

if not accounts:
    print("✗ Аккаунты не найдены!")
    sys.exit(1)

account = accounts[0]
print(f"✓ Загружен аккаунт: {account.username}")
print(f"  Пароль: {'*' * len(account.password)}")
print(f"  Shared secret: {'Да' if account.shared_secret else 'Нет'}")
print()

# Создаем менеджер (НЕ headless для визуального контроля)
print("2. Инициализация браузера (с GUI для отладки)...")
manager = SteamManager(headless=False)  # <-- Браузер будет виден!
print()

try:
    print("3. Попытка авторизации...")
    print(f"   Username: {account.username}")
    print(f"   Shared secret: {account.shared_secret[:20]}..." if account.shared_secret else "   Shared secret: None")
    print()

    success = manager.login(account.username, account.password, account.shared_secret)

    print()
    if success:
        print("✓ АВТОРИЗАЦИЯ УСПЕШНА!")
        print()
        print("Браузер останется открытым 10 секунд...")
        time.sleep(10)
    else:
        print("✗ АВТОРИЗАЦИЯ НЕ УДАЛАСЬ")
        print()
        print("Браузер останется открытым 30 секунд для диагностики...")
        time.sleep(30)

except Exception as e:
    print(f"\n✗ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

    print()
    print("Браузер останется открытым 30 секунд для диагностики...")
    time.sleep(30)

finally:
    print()
    print("Закрытие браузера...")
    manager.logout_all()
    print("Готово!")
