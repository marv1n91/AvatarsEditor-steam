"""
Менеджер профильных данных для Steam
"""
import os
import random
import logging

logger = logging.getLogger(__name__)


class ProfileManager:
    """Класс для управления профильными данными"""

    def __init__(self, profile_names_file: str = 'profile_data/profile_names.txt',
                 real_names_file: str = 'profile_data/real_names.txt',
                 about_me_file: str = 'profile_data/about_me.txt'):
        """
        Инициализация менеджера профилей

        Args:
            profile_names_file: Путь к файлу с именами профилей
            real_names_file: Путь к файлу с настоящими именами
            about_me_file: Путь к файлу с текстами "О себе"
        """
        self.profile_names_file = profile_names_file
        self.real_names_file = real_names_file
        self.about_me_file = about_me_file

        self.profile_names = []
        self.real_names = []
        self.about_me_texts = []

    def load_profile_names(self) -> list:
        """Загрузка имен профилей из файла"""
        try:
            if not os.path.exists(self.profile_names_file):
                logger.warning(f"⚠️ Файл {self.profile_names_file} не найден")
                return []

            with open(self.profile_names_file, 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            self.profile_names = names
            logger.info(f"✓ Загружено имен профилей: {len(names)}")
            return names

        except Exception as e:
            logger.error(f"✗ Ошибка загрузки имен профилей: {str(e)}")
            return []

    def load_real_names(self) -> list:
        """Загрузка настоящих имен из файла"""
        try:
            if not os.path.exists(self.real_names_file):
                logger.warning(f"⚠️ Файл {self.real_names_file} не найден")
                return []

            with open(self.real_names_file, 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            self.real_names = names
            logger.info(f"✓ Загружено настоящих имен: {len(names)}")
            return names

        except Exception as e:
            logger.error(f"✗ Ошибка загрузки настоящих имен: {str(e)}")
            return []

    def load_about_me_texts(self) -> list:
        """Загрузка текстов 'О себе' из файла"""
        try:
            if not os.path.exists(self.about_me_file):
                logger.warning(f"⚠️ Файл {self.about_me_file} не найден")
                return []

            with open(self.about_me_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Разделяем тексты по разделителю ---
            texts = [text.strip() for text in content.split('---') if text.strip() and not text.strip().startswith('#')]

            self.about_me_texts = texts
            logger.info(f"✓ Загружено текстов 'О себе': {len(texts)}")
            return texts

        except Exception as e:
            logger.error(f"✗ Ошибка загрузки текстов 'О себе': {str(e)}")
            return []

    def get_random_profile_name(self) -> str:
        """Получить случайное имя профиля"""
        if not self.profile_names:
            self.load_profile_names()

        if self.profile_names:
            return random.choice(self.profile_names)
        return ""

    def get_random_real_name(self) -> str:
        """Получить случайное настоящее имя"""
        if not self.real_names:
            self.load_real_names()

        if self.real_names:
            return random.choice(self.real_names)
        return ""

    def get_random_about_me(self) -> str:
        """Получить случайный текст 'О себе'"""
        if not self.about_me_texts:
            self.load_about_me_texts()

        if self.about_me_texts:
            return random.choice(self.about_me_texts)
        return ""

    def get_unique_profile_data(self, count: int) -> list:
        """
        Получить уникальные наборы данных для профилей

        Args:
            count: Количество наборов данных

        Returns:
            Список словарей с данными профилей
        """
        profile_names = self.profile_names or self.load_profile_names()
        real_names = self.real_names or self.load_real_names()
        about_me_texts = self.about_me_texts or self.load_about_me_texts()

        # Если данных меньше чем аккаунтов, используем повторно
        result = []
        for i in range(count):
            profile_data = {
                'profile_name': profile_names[i % len(profile_names)] if profile_names else "",
                'real_name': real_names[i % len(real_names)] if real_names else "",
                'about_me': about_me_texts[i % len(about_me_texts)] if about_me_texts else ""
            }
            result.append(profile_data)

        return result
