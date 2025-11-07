"""
Модуль для работы с Steam API и сменой аватарок
"""
import requests
import json
import os
from typing import Dict, Optional
from steampy.client import SteamClient
from steampy.exceptions import InvalidCredentials
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SteamManager:
    """Класс для управления Steam аккаунтами и аватарками"""

    def __init__(self):
        self.clients: Dict[str, SteamClient] = {}

    def login(self, username: str, password: str, shared_secret: str = "") -> bool:
        """
        Авторизация в Steam аккаунте

        Args:
            username: Логин Steam
            password: Пароль Steam
            shared_secret: Shared secret для Steam Guard (если включен)

        Returns:
            True если авторизация успешна, False в противном случае
        """
        try:
            client = SteamClient(api_key=None)

            if shared_secret:
                client.login(username, password, shared_secret)
            else:
                client.login(username, password, '')

            self.clients[username] = client
            logger.info(f"✓ Успешная авторизация: {username}")
            return True

        except InvalidCredentials:
            logger.error(f"✗ Неверные учетные данные: {username}")
            return False
        except Exception as e:
            logger.error(f"✗ Ошибка авторизации {username}: {str(e)}")
            return False

    def change_avatar(self, username: str, avatar_path: str) -> bool:
        """
        Смена аватарки Steam аккаунта

        Args:
            username: Логин Steam аккаунта
            avatar_path: Путь к файлу аватарки

        Returns:
            True если смена успешна, False в противном случае
        """
        if username not in self.clients:
            logger.error(f"✗ Аккаунт {username} не авторизован")
            return False

        if not os.path.exists(avatar_path):
            logger.error(f"✗ Файл аватарки не найден: {avatar_path}")
            return False

        try:
            client = self.clients[username]

            # Получаем Steam ID
            steam_id = client.steam_guard['steamid']

            # Загружаем аватарку через Steam Web API
            success = self._upload_avatar(client, steam_id, avatar_path)

            if success:
                logger.info(f"✓ Аватарка изменена для {username}")
                return True
            else:
                logger.error(f"✗ Не удалось изменить аватарку для {username}")
                return False

        except Exception as e:
            logger.error(f"✗ Ошибка смены аватарки для {username}: {str(e)}")
            return False

    def _upload_avatar(self, client: SteamClient, steam_id: str, avatar_path: str) -> bool:
        """
        Внутренний метод для загрузки аватарки через Steam API

        Args:
            client: Экземпляр SteamClient
            steam_id: Steam ID пользователя
            avatar_path: Путь к файлу аватарки

        Returns:
            True если загрузка успешна
        """
        try:
            # URL для загрузки аватарки
            upload_url = "https://steamcommunity.com/actions/FileUploader"

            # Подготавливаем файл
            with open(avatar_path, 'rb') as f:
                files = {
                    'avatar': (os.path.basename(avatar_path), f, 'image/jpeg')
                }

                data = {
                    'type': 'player_avatar_image',
                    'sId': steam_id,
                    'sessionid': client._session.cookies.get('sessionid'),
                    'doSub': '1',
                    'json': '1'
                }

                # Отправляем запрос
                response = client._session.post(upload_url, files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    return result.get('success', False)

            return False

        except Exception as e:
            logger.error(f"Ошибка загрузки аватарки: {str(e)}")
            return False

    def logout(self, username: str):
        """Выход из аккаунта"""
        if username in self.clients:
            try:
                self.clients[username].logout()
                del self.clients[username]
                logger.info(f"✓ Выход из аккаунта: {username}")
            except Exception as e:
                logger.error(f"✗ Ошибка выхода из {username}: {str(e)}")

    def logout_all(self):
        """Выход из всех аккаунтов"""
        for username in list(self.clients.keys()):
            self.logout(username)
