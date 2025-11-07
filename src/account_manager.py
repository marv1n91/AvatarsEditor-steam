"""
Модуль для управления аккаунтами Steam
"""
import os
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Account:
    """Класс для представления Steam аккаунта"""

    def __init__(self, username: str, password: str, shared_secret: str = ""):
        self.username = username
        self.password = password
        self.shared_secret = shared_secret

    def __repr__(self):
        return f"Account(username='{self.username}')"

    def to_dict(self) -> Dict:
        """Преобразование в словарь"""
        return {
            'username': self.username,
            'password': self.password,
            'shared_secret': self.shared_secret
        }


class AccountManager:
    """Класс для управления списком аккаунтов"""

    def __init__(self, accounts_file: str = "accounts/accounts.txt"):
        self.accounts_file = accounts_file
        self.accounts: List[Account] = []

    def load_accounts(self) -> List[Account]:
        """
        Загрузка аккаунтов из файла

        Поддерживаемые форматы:
        1. username:password
        2. username:password:shared_secret
        3. JSON формат: {"username": "user", "password": "pass", "shared_secret": "secret"}

        Returns:
            Список загруженных аккаунтов
        """
        if not os.path.exists(self.accounts_file):
            logger.error(f"✗ Файл с аккаунтами не найден: {self.accounts_file}")
            return []

        self.accounts = []

        try:
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                # Попытка загрузить как JSON
                if content.startswith('[') or content.startswith('{'):
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            for item in data:
                                account = Account(
                                    username=item['username'],
                                    password=item['password'],
                                    shared_secret=item.get('shared_secret', '')
                                )
                                self.accounts.append(account)
                        else:
                            account = Account(
                                username=data['username'],
                                password=data['password'],
                                shared_secret=data.get('shared_secret', '')
                            )
                            self.accounts.append(account)
                    except json.JSONDecodeError:
                        logger.error("✗ Ошибка парсинга JSON")
                        return []
                else:
                    # Загрузка из текстового формата
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue

                        parts = line.split(':')
                        if len(parts) >= 2:
                            username = parts[0]
                            password = parts[1]
                            shared_secret = parts[2] if len(parts) > 2 else ""

                            account = Account(username, password, shared_secret)
                            self.accounts.append(account)

            logger.info(f"✓ Загружено аккаунтов: {len(self.accounts)}")
            return self.accounts

        except Exception as e:
            logger.error(f"✗ Ошибка загрузки аккаунтов: {str(e)}")
            return []

    def save_accounts(self):
        """Сохранение аккаунтов в файл"""
        try:
            os.makedirs(os.path.dirname(self.accounts_file), exist_ok=True)

            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                for account in self.accounts:
                    if account.shared_secret:
                        f.write(f"{account.username}:{account.password}:{account.shared_secret}\n")
                    else:
                        f.write(f"{account.username}:{account.password}\n")

            logger.info(f"✓ Аккаунты сохранены в {self.accounts_file}")

        except Exception as e:
            logger.error(f"✗ Ошибка сохранения аккаунтов: {str(e)}")

    def add_account(self, username: str, password: str, shared_secret: str = ""):
        """Добавление нового аккаунта"""
        account = Account(username, password, shared_secret)
        self.accounts.append(account)
        logger.info(f"✓ Аккаунт добавлен: {username}")

    def get_accounts(self) -> List[Account]:
        """Получение списка всех аккаунтов"""
        return self.accounts

    def get_account_count(self) -> int:
        """Получение количества аккаунтов"""
        return len(self.accounts)
