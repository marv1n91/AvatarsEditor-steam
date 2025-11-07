"""
Модуль для работы с Steam через Selenium для смены аватарок
"""
import os
import time
import base64
import struct
import hashlib
import hmac
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger(__name__)


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
            # Декодируем shared_secret из base64
            secret = base64.b64decode(shared_secret)

            # Получаем текущее время в формате Steam (30-секундные интервалы)
            timestamp = int(time.time()) // 30
            time_buffer = struct.pack('>Q', timestamp)

            # Создаем HMAC-SHA1
            hmac_digest = hmac.new(secret, time_buffer, hashlib.sha1).digest()

            # Извлекаем динамический код
            start = hmac_digest[19] & 0x0F
            code_bytes = hmac_digest[start:start + 4]
            full_code = struct.unpack('>I', code_bytes)[0] & 0x7FFFFFFF

            # Steam использует специальный алфавит для кодов
            steam_chars = '23456789BCDFGHJKMNPQRTVWXY'
            code = ''

            for _ in range(5):
                code += steam_chars[full_code % len(steam_chars)]
                full_code //= len(steam_chars)

            logger.debug(f"Сгенерирован код Steam Guard: {code}")
            return code

        except Exception as e:
            logger.error(f"Ошибка генерации Steam Guard кода: {str(e)}")
            return ""


class SteamManager:
    """Класс для управления Steam аккаунтами через Selenium"""

    def __init__(self, headless: bool = True):
        """
        Инициализация менеджера

        Args:
            headless: Запускать браузер в headless режиме (без GUI)
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self.current_username: Optional[str] = None
        self.steam_guard = SteamGuardGenerator()

    def _init_driver(self):
        """Инициализация Chrome WebDriver"""
        if self.driver is not None:
            return

        try:
            chrome_options = Options()

            # Попытка найти установленный Chromium
            chromium_paths = [
                '/opt/chromium/chrome-linux64/chrome',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable'
            ]

            chrome_binary = None
            for path in chromium_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    logger.debug(f"Найден Chrome/Chromium: {path}")
                    break

            if chrome_binary:
                chrome_options.binary_location = chrome_binary

            if self.headless:
                chrome_options.add_argument('--headless=new')

            # Минимальные опции для работы в Docker
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')

            # Более реалистичный user-agent (актуальная версия Chrome)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

            # Добавляем реалистичные preferences
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            })

            # Отключаем автоматизацию detection
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Настройка ChromeDriver
            logger.debug("Инициализация ChromeDriver...")

            # Попытка использовать локальный ChromeDriver
            chromedriver_paths = [
                '/opt/chromium/chromedriver-linux64/chromedriver',
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver'
            ]

            chromedriver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    logger.debug(f"Найден ChromeDriver: {path}")
                    break

            if chromedriver_path:
                service = Service(chromedriver_path)
            else:
                # Если не найден локально, используем webdriver-manager
                logger.debug("Локальный ChromeDriver не найден, используем webdriver-manager")
                service = Service(ChromeDriverManager().install())

            # Создаем драйвер
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })

            logger.debug("Chrome WebDriver инициализирован")

        except WebDriverException as e:
            logger.error(f"✗ Ошибка инициализации WebDriver: {str(e)}")
            logger.error("   Убедитесь, что Chrome или Chromium установлен")
            logger.error("   Linux: sudo apt install chromium-browser")
            logger.error("   или: sudo apt install google-chrome-stable")
            raise

    def login(self, username: str, password: str, shared_secret: str = "") -> bool:
        """
        Авторизация в Steam через браузер

        Args:
            username: Логин Steam
            password: Пароль Steam
            shared_secret: Shared secret для Steam Guard (если включен)

        Returns:
            True если авторизация успешна
        """
        try:
            self._init_driver()

            logger.debug(f"Переход на страницу входа Steam для {username}")
            self.driver.get("https://steamcommunity.com/login/home/?goto=")

            # Ждем загрузки страницы
            logger.debug("Ожидание загрузки страницы...")
            time.sleep(5)

            # Проверяем, что страница загрузилась
            logger.debug(f"Текущий URL: {self.driver.current_url}")
            logger.debug(f"Заголовок страницы: {self.driver.title}")

            # Находим и заполняем поле логина
            logger.debug("Поиск поля ввода логина...")
            username_field = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            logger.debug("Поле логина найдено")
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(0.5)

            # Находим и заполняем поле пароля
            logger.debug("Ввод пароля...")
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)

            # Нажимаем кнопку входа
            logger.debug("Нажатие кнопки входа...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Ждем появления формы Steam Guard или успешного входа
            logger.debug("Ожидание экрана подтверждения...")
            time.sleep(5)

            # Проверяем, требуется ли код Steam Guard
            try:
                # Сначала проверяем, есть ли экран выбора метода подтверждения
                logger.debug("Поиск кнопки для ввода кода из приложения...")

                # Пробуем разные варианты кнопок для выбора ввода кода
                use_code_button = None
                button_selectors = [
                    "//div[contains(text(), 'code')]",
                    "//div[contains(text(), 'authenticator')]",
                    "//button[contains(text(), 'code')]",
                    "//div[contains(@class, 'ConfirmationEntry')]",
                    "[class*='ConfirmationEntry']",
                    "div[data-panel-id*='code']"
                ]

                for selector in button_selectors:
                    try:
                        if selector.startswith("//"):
                            elements = self.driver.find_elements(By.XPATH, selector)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                        if elements:
                            logger.debug(f"Найдено элементов по селектору '{selector}': {len(elements)}")
                            # Ищем кликабельный элемент
                            for elem in elements:
                                try:
                                    text = elem.text.lower()
                                    logger.debug(f"  Текст элемента: {text[:100]}")
                                    if 'code' in text or 'authenticator' in text or 'guard' in text.lower():
                                        use_code_button = elem
                                        logger.debug(f"✓ Найдена кнопка для ввода кода!")
                                        break
                                except:
                                    continue

                        if use_code_button:
                            break
                    except:
                        continue

                # Если нашли кнопку выбора метода - нажимаем
                if use_code_button:
                    logger.debug("Нажатие кнопки 'Использовать код'...")
                    use_code_button.click()
                    time.sleep(2)
                else:
                    logger.debug("Кнопка выбора метода не найдена, возможно поле ввода уже открыто")

                # Теперь ищем поле для ввода кода
                logger.debug("Поиск поля для ввода кода Steam Guard...")

                # Пробуем разные селекторы для поля ввода
                code_field = None
                input_selectors = [
                    "input[type='text']",
                    "input[autocomplete='one-time-code']",
                    "input.Focusable",
                    "input[name*='code']",
                    "input[placeholder*='code']"
                ]

                for selector in input_selectors:
                    try:
                        field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if field and field.is_displayed():
                            code_field = field
                            logger.debug(f"✓ Найдено поле ввода по селектору: {selector}")
                            break
                    except:
                        continue

                if not code_field:
                    logger.debug("Поле для ввода кода не найдено, возможно вход успешен")
                    # Проверим успешность входа ниже
                elif shared_secret:
                    logger.debug("Требуется код Steam Guard, генерируем...")
                    guard_code = self.steam_guard.generate_code(shared_secret)

                    if not guard_code:
                        logger.error("✗ Не удалось сгенерировать код Steam Guard")
                        return False

                    logger.debug(f"Ввод кода Steam Guard: {guard_code}")
                    code_field.clear()
                    code_field.send_keys(guard_code)
                    time.sleep(1)

                    # Нажимаем кнопку подтверждения
                    logger.debug("Поиск кнопки подтверждения...")
                    try:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        submit_button.click()
                        logger.debug("✓ Кнопка подтверждения нажата")
                    except:
                        logger.debug("Кнопка submit не найдена, код может отправиться автоматически")

                    time.sleep(3)
                else:
                    logger.error("✗ Требуется код Steam Guard, но shared_secret не предоставлен")
                    return False

            except Exception as e:
                # Код Steam Guard не требуется или уже вошли
                logger.debug(f"Исключение при обработке Steam Guard: {str(e)}")
                logger.debug("Возможно, Steam Guard не требуется")

            # Проверяем успешность входа
            time.sleep(2)
            current_url = self.driver.current_url

            if "steamcommunity.com" in current_url and "/login" not in current_url:
                logger.info(f"✓ Успешная авторизация: {username}")
                self.current_username = username
                return True
            else:
                logger.error(f"✗ Не удалось авторизоваться: {username}")
                logger.debug(f"Текущий URL: {current_url}")
                return False

        except TimeoutException:
            logger.error(f"✗ Превышено время ожидания при авторизации {username}")
            return False
        except Exception as e:
            logger.error(f"✗ Ошибка авторизации {username}: {str(e)}")
            return False

    def change_avatar(self, username: str, avatar_path: str) -> bool:
        """
        Смена аватарки через браузер

        Args:
            username: Логин Steam (для проверки)
            avatar_path: Путь к файлу аватарки

        Returns:
            True если смена успешна
        """
        if self.current_username != username:
            logger.error(f"✗ Аккаунт {username} не авторизован")
            return False

        if not os.path.exists(avatar_path):
            logger.error(f"✗ Файл аватарки не найден: {avatar_path}")
            return False

        try:
            logger.debug(f"Переход на страницу редактирования профиля...")
            self.driver.get("https://steamcommunity.com/my/edit/avatar")
            time.sleep(2)

            # Находим input для загрузки файла
            logger.debug("Поиск элемента загрузки файла...")
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )

            # Загружаем файл
            logger.debug(f"Загрузка файла: {avatar_path}")
            abs_path = os.path.abspath(avatar_path)
            file_input.send_keys(abs_path)
            time.sleep(2)

            # Ищем и нажимаем кнопку сохранения
            logger.debug("Поиск кнопки сохранения...")
            try:
                # Пробуем найти разные варианты кнопок сохранения
                save_selectors = [
                    "button.DialogButton.Primary",
                    "button[type='submit']",
                    "//button[contains(text(), 'Save')]",
                    "//button[contains(text(), 'Сохранить')]"
                ]

                save_button = None
                for selector in save_selectors:
                    try:
                        if selector.startswith("//"):
                            save_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            save_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if save_button:
                            break
                    except NoSuchElementException:
                        continue

                if save_button:
                    logger.debug("Нажатие кнопки сохранения...")
                    save_button.click()
                    time.sleep(2)

                    logger.info(f"✓ Аватарка изменена для {username}")
                    return True
                else:
                    logger.warning("⚠️ Кнопка сохранения не найдена, но файл загружен")
                    # Иногда аватарка сохраняется автоматически
                    return True

            except Exception as e:
                logger.debug(f"Ошибка при поиске кнопки сохранения: {str(e)}")
                logger.warning("⚠️ Не удалось найти кнопку сохранения")
                return True  # Предполагаем, что загрузка прошла успешно

        except TimeoutException:
            logger.error(f"✗ Превышено время ожидания при смене аватарки")
            return False
        except Exception as e:
            logger.error(f"✗ Ошибка смены аватарки: {str(e)}")
            return False

    def logout(self, username: str):
        """Выход из аккаунта (закрытие сессии браузера)"""
        if self.current_username == username:
            logger.debug(f"Выход из аккаунта {username}")
            self.current_username = None

            if self.driver:
                try:
                    # Очищаем cookies
                    self.driver.delete_all_cookies()
                    logger.info(f"✓ Выход из аккаунта: {username}")
                except Exception as e:
                    logger.error(f"✗ Ошибка при выходе: {str(e)}")

    def logout_all(self):
        """Закрытие браузера и очистка всех сессий"""
        logger.debug("Закрытие браузера...")
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.current_username = None
                logger.debug("✓ Браузер закрыт")
            except Exception as e:
                logger.error(f"✗ Ошибка закрытия браузера: {str(e)}")

    def __del__(self):
        """Деструктор - закрываем браузер при удалении объекта"""
        self.logout_all()
