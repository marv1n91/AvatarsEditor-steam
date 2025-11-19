"""
Модуль для работы с Steam Points через API
Использует асинхронные запросы для высокой производительности
"""
import asyncio
import aiohttp
import json
import logging
import time
import base64
import struct
import hashlib
import hmac
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SteamGift:
    """Представление подарка Steam Points"""
    defid: int
    name: str
    cost: int
    description: str = ""

    def __repr__(self):
        return f"SteamGift(name='{self.name}', cost={self.cost})"


class SteamGuardGenerator:
    """Генератор кодов Steam Guard из shared_secret"""

    @staticmethod
    def generate_code(shared_secret: str) -> str:
        """
        Генерирует код Steam Guard из shared_secret

        Args:
            shared_secret: Base64 закодированный shared secret

        Returns:
            5-значный код Steam Guard
        """
        if not shared_secret:
            return ""

        try:
            # Исправляем padding для base64
            missing_padding = len(shared_secret) % 4
            if missing_padding:
                shared_secret += '=' * (4 - missing_padding)

            secret = base64.b64decode(shared_secret)
            timestamp = int(time.time()) // 30
            time_buffer = struct.pack('>Q', timestamp)

            hmac_digest = hmac.new(secret, time_buffer, hashlib.sha1).digest()

            start = hmac_digest[19] & 0x0F
            code_bytes = hmac_digest[start:start + 4]
            full_code = struct.unpack('>I', code_bytes)[0] & 0x7FFFFFFF

            steam_chars = '23456789BCDFGHJKMNPQRTVWXY'
            code = ''

            for _ in range(5):
                code += steam_chars[full_code % len(steam_chars)]
                full_code //= len(steam_chars)

            return code

        except Exception as e:
            logger.error(f"Ошибка генерации Steam Guard кода: {str(e)}")
            return ""


class SteamPointsManager:
    """Класс для работы с Steam Points через API"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.steam_guard = SteamGuardGenerator()

    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _init_session(self):
        """Инициализация aiohttp сессии"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                    'Origin': 'https://steamcommunity.com',
                }
            )

    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None

    async def login(self, username: str, password: str, shared_secret: str = "") -> Optional[Dict]:
        """
        Авторизация в Steam через API

        Args:
            username: Логин Steam
            password: Пароль Steam
            shared_secret: Shared secret для Steam Guard

        Returns:
            Dict с cookies и токенами или None при ошибке
        """
        await self._init_session()

        try:
            # Шаг 1: Получаем RSA ключ для шифрования пароля
            logger.debug(f"Получение RSA ключа для {username}...")
            async with self.session.post(
                'https://steamcommunity.com/login/getrsakey/',
                data={'username': username}
            ) as response:
                rsa_data = await response.json()

            if not rsa_data.get('success'):
                logger.error(f"Не удалось получить RSA ключ для {username}")
                return None

            # Шаг 2: Шифруем пароль (для упрощения используем base64)
            # В продакшене нужно использовать RSA шифрование
            encrypted_password = base64.b64encode(password.encode()).decode()

            # Шаг 3: Отправляем запрос на авторизацию
            logger.debug(f"Авторизация {username}...")
            login_data = {
                'username': username,
                'password': encrypted_password,
                'emailauth': '',
                'emailsteamid': '',
                'captchagid': '-1',
                'captcha_text': '',
                'loginfriendlyname': 'SteamPoints Manager',
                'rsatimestamp': rsa_data.get('timestamp', ''),
                'remember_login': 'true',
                'donotcache': str(int(time.time() * 1000))
            }

            # Если есть Steam Guard, добавляем код
            if shared_secret:
                guard_code = self.steam_guard.generate_code(shared_secret)
                login_data['twofactorcode'] = guard_code
                logger.debug(f"Используется Steam Guard код: {guard_code}")

            async with self.session.post(
                'https://steamcommunity.com/login/dologin/',
                data=login_data
            ) as response:
                result = await response.json()

            if result.get('success'):
                logger.info(f"✓ Успешная авторизация: {username}")

                # Извлекаем cookies
                cookies = {}
                for cookie in self.session.cookie_jar:
                    cookies[cookie.key] = cookie.value

                return {
                    'steamid': result.get('transfer_parameters', {}).get('steamid'),
                    'cookies': cookies,
                    'session': result
                }
            else:
                logger.error(f"✗ Ошибка авторизации {username}: {result.get('message', 'Неизвестная ошибка')}")
                return None

        except Exception as e:
            logger.error(f"✗ Исключение при авторизации {username}: {str(e)}")
            return None

    async def get_points_balance(self, steamid: str) -> Optional[int]:
        """
        Получение баланса Steam Points

        Args:
            steamid: Steam ID пользователя

        Returns:
            Баланс очков или None при ошибке
        """
        await self._init_session()

        try:
            async with self.session.get(
                f'https://api.steampowered.com/ILoyaltyRewardsService/GetSummary/v1/',
                params={'steamid': steamid}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    points = data.get('response', {}).get('summary', {}).get('points', 0)
                    logger.debug(f"Баланс очков для {steamid}: {points}")
                    return points
                else:
                    logger.error(f"Ошибка получения баланса: статус {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Исключение при получении баланса: {str(e)}")
            return None

    async def get_available_gifts(self) -> List[SteamGift]:
        """
        Получение списка доступных подарков Steam Points

        Returns:
            Список доступных подарков
        """
        await self._init_session()

        try:
            # Получаем список доступных наград
            async with self.session.get(
                'https://api.steampowered.com/ILoyaltyRewardsService/GetRewardsList/v1/'
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    definitions = data.get('response', {}).get('definitions', [])

                    gifts = []
                    for item in definitions:
                        # Фильтруем только подарки (не профильные элементы)
                        if item.get('type') == 10:  # 10 = подарки
                            gift = SteamGift(
                                defid=item.get('defid'),
                                name=item.get('community_item_data', {}).get('item_name', 'Unknown'),
                                cost=item.get('point_cost', 0),
                                description=item.get('community_item_data', {}).get('item_description', '')
                            )
                            gifts.append(gift)

                    logger.debug(f"Найдено подарков: {len(gifts)}")
                    return sorted(gifts, key=lambda x: x.cost)
                else:
                    logger.error(f"Ошибка получения списка подарков: статус {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Исключение при получении списка подарков: {str(e)}")
            return []

    async def find_best_gift(self, points_balance: int, gifts: List[SteamGift]) -> Optional[SteamGift]:
        """
        Находит наиболее подходящий подарок по балансу очков

        Args:
            points_balance: Баланс очков
            gifts: Список доступных подарков

        Returns:
            Наиболее подходящий подарок или None
        """
        if not gifts:
            return None

        # Фильтруем подарки, которые можно купить
        affordable_gifts = [g for g in gifts if g.cost <= points_balance]

        if not affordable_gifts:
            logger.warning(f"Нет подарков доступных для {points_balance} очков")
            return None

        # Выбираем самый дорогой из доступных
        best_gift = max(affordable_gifts, key=lambda x: x.cost)
        logger.debug(f"Лучший подарок: {best_gift.name} ({best_gift.cost} очков)")
        return best_gift

    async def send_gift(self, defid: int, recipient_steamid: str, sender_steamid: str,
                       sender_name: str = "", message: str = "") -> bool:
        """
        Отправка подарка другому пользователю

        Args:
            defid: ID определения подарка
            recipient_steamid: Steam ID получателя
            sender_steamid: Steam ID отправителя
            sender_name: Имя отправителя
            message: Сообщение к подарку

        Returns:
            True если подарок отправлен успешно
        """
        await self._init_session()

        try:
            # Готовим данные для отправки подарка
            gift_data = {
                'defid': defid,
                'receiversteamid': recipient_steamid,
                'sendersteamid': sender_steamid,
                'sender_name': sender_name or 'Anonymous',
                'message': message
            }

            async with self.session.post(
                'https://api.steampowered.com/ILoyaltyRewardsService/RedeemPointsForProfileCustomization/v1/',
                json=gift_data
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    if result.get('response', {}).get('success'):
                        logger.info(f"✓ Подарок успешно отправлен: {defid} -> {recipient_steamid}")
                        return True
                    else:
                        logger.error(f"✗ Ошибка отправки подарка: {result}")
                        return False
                else:
                    logger.error(f"✗ Ошибка HTTP при отправке подарка: статус {response.status}")
                    return False

        except Exception as e:
            logger.error(f"✗ Исключение при отправке подарка: {str(e)}")
            return False

    async def process_account(self, username: str, password: str, shared_secret: str,
                             recipient_steamid: str) -> Dict:
        """
        Обработка одного аккаунта: проверка баланса и отправка подарка

        Args:
            username: Логин
            password: Пароль
            shared_secret: Shared secret для Steam Guard
            recipient_steamid: Steam ID получателя подарка

        Returns:
            Dict с результатами обработки
        """
        result = {
            'username': username,
            'success': False,
            'points_balance': 0,
            'gift_sent': None,
            'error': None
        }

        try:
            # Авторизация
            auth_data = await self.login(username, password, shared_secret)
            if not auth_data:
                result['error'] = 'Ошибка авторизации'
                return result

            steamid = auth_data.get('steamid')
            if not steamid:
                result['error'] = 'Не удалось получить Steam ID'
                return result

            # Получаем баланс очков
            points_balance = await self.get_points_balance(steamid)
            if points_balance is None:
                result['error'] = 'Не удалось получить баланс очков'
                return result

            result['points_balance'] = points_balance

            if points_balance == 0:
                result['error'] = 'Баланс очков равен 0'
                return result

            # Получаем список подарков
            gifts = await self.get_available_gifts()
            if not gifts:
                result['error'] = 'Не удалось получить список подарков'
                return result

            # Находим лучший подарок
            best_gift = await self.find_best_gift(points_balance, gifts)
            if not best_gift:
                result['error'] = f'Нет подарков для {points_balance} очков'
                return result

            # Отправляем подарок
            gift_sent = await self.send_gift(
                best_gift.defid,
                recipient_steamid,
                steamid,
                username,
                f"Подарок от {username}"
            )

            if gift_sent:
                result['success'] = True
                result['gift_sent'] = {
                    'name': best_gift.name,
                    'cost': best_gift.cost
                }
            else:
                result['error'] = 'Не удалось отправить подарок'

            return result

        except Exception as e:
            result['error'] = f'Исключение: {str(e)}'
            logger.error(f"Ошибка обработки аккаунта {username}: {str(e)}")
            return result


async def process_accounts_batch(accounts: List[Tuple[str, str, str]],
                                 recipient_steamid: str,
                                 max_concurrent: int = 5) -> List[Dict]:
    """
    Асинхронная обработка пакета аккаунтов

    Args:
        accounts: Список кортежей (username, password, shared_secret)
        recipient_steamid: Steam ID получателя подарков
        max_concurrent: Максимальное количество одновременных операций

    Returns:
        Список результатов обработки
    """
    results = []

    # Создаем семафор для ограничения количества одновременных операций
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(account_data):
        async with semaphore:
            async with SteamPointsManager() as manager:
                username, password, shared_secret = account_data
                return await manager.process_account(
                    username, password, shared_secret, recipient_steamid
                )

    # Запускаем все задачи одновременно
    tasks = [process_with_semaphore(acc) for acc in accounts]
    results = await asyncio.gather(*tasks)

    return results
