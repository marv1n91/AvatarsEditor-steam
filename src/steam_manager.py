"""
Модуль для работы с Steam API и сменой аватарок
"""
import requests
import json
import os
import time
from typing import Dict, Optional
from steampy.client import SteamClient
from steampy.exceptions import InvalidCredentials, ApiException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SteamManager:
    """Класс для управления Steam аккаунтами и аватарками"""

    def __init__(self):
        self.clients: Dict[str, SteamClient] = {}
        self.max_retries = 3  # Максимальное количество попыток

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
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Попытка авторизации {attempt + 1}/{self.max_retries} для {username}")

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

            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Ошибка парсинга JSON (попытка {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Экспоненциальная задержка
                    logger.info(f"   Ожидание {wait_time} секунд перед повторной попыткой...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"✗ Не удалось авторизоваться после {self.max_retries} попыток")
                    logger.error(f"   Возможные причины:")
                    logger.error(f"   - Steam API временно недоступен")
                    logger.error(f"   - Проблемы с сетевым подключением")
                    logger.error(f"   - Требуется Steam Guard код (добавьте shared_secret)")
                    return False

            except ApiException as e:
                logger.error(f"✗ Ошибка Steam API для {username}: {str(e)}")
                return False

            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Сетевая ошибка (попытка {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"   Ожидание {wait_time} секунд перед повторной попыткой...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"✗ Сетевая ошибка после {self.max_retries} попыток")
                    return False

            except Exception as e:
                error_msg = str(e)
                logger.error(f"✗ Неожиданная ошибка авторизации {username}: {error_msg}")

                # Дополнительная информация для отладки
                if "Expecting value" in error_msg:
                    logger.error(f"   Подсказка: Steam вернул пустой или некорректный ответ")
                    logger.error(f"   Попробуйте:")
                    logger.error(f"   1. Проверить интернет-соединение")
                    logger.error(f"   2. Убедиться, что аккаунт не заблокирован")
                    logger.error(f"   3. Добавить shared_secret для Steam Guard")
                    logger.error(f"   4. Увеличить задержку между аккаунтами")

                return False

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
                response = client._session.post(upload_url, files=files, data=data, timeout=30)

                logger.debug(f"Ответ сервера: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        success = result.get('success', False)

                        if not success:
                            logger.warning(f"Steam вернул success=False: {result}")

                        return success
                    except json.JSONDecodeError:
                        logger.error(f"Не удалось распарсить ответ Steam при загрузке аватарки")
                        logger.debug(f"Содержимое ответа: {response.text[:200]}")
                        return False
                else:
                    logger.error(f"Ошибка HTTP {response.status_code} при загрузке аватарки")
                    return False

            return False

        except requests.exceptions.Timeout:
            logger.error(f"Timeout при загрузке аватарки (превышено 30 секунд)")
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
