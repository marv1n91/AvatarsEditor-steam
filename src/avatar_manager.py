"""
Модуль для управления аватарками
"""
import os
import random
from typing import List
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvatarManager:
    """Класс для управления аватарками"""

    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    MAX_SIZE = (184, 184)  # Максимальный размер аватарки Steam

    def __init__(self, avatars_dir: str = "avatars"):
        self.avatars_dir = avatars_dir
        self.avatars: List[str] = []

    def load_avatars(self) -> List[str]:
        """
        Загрузка списка аватарок из директории

        Returns:
            Список путей к файлам аватарок
        """
        if not os.path.exists(self.avatars_dir):
            logger.error(f"✗ Директория с аватарками не найдена: {self.avatars_dir}")
            os.makedirs(self.avatars_dir, exist_ok=True)
            logger.info(f"✓ Создана директория: {self.avatars_dir}")
            return []

        self.avatars = []

        try:
            for filename in os.listdir(self.avatars_dir):
                file_path = os.path.join(self.avatars_dir, filename)

                # Проверяем, что это файл
                if not os.path.isfile(file_path):
                    continue

                # Проверяем расширение
                _, ext = os.path.splitext(filename)
                if ext.lower() in self.SUPPORTED_FORMATS:
                    self.avatars.append(file_path)

            logger.info(f"✓ Найдено аватарок: {len(self.avatars)}")
            return self.avatars

        except Exception as e:
            logger.error(f"✗ Ошибка загрузки аватарок: {str(e)}")
            return []

    def get_random_avatar(self) -> str:
        """
        Получение случайной аватарки

        Returns:
            Путь к случайной аватарке
        """
        if not self.avatars:
            logger.error("✗ Нет доступных аватарок")
            return ""

        return random.choice(self.avatars)

    def get_unique_avatars(self, count: int) -> List[str]:
        """
        Получение уникальных аватарок (без повторений)

        Args:
            count: Количество нужных аватарок

        Returns:
            Список путей к аватаркам
        """
        if count > len(self.avatars):
            logger.warning(f"⚠ Запрошено {count} аватарок, но доступно только {len(self.avatars)}")
            logger.warning("⚠ Некоторые аватарки будут использованы повторно")

            # Возвращаем все аватарки + случайные для недостающих
            result = self.avatars.copy()
            remaining = count - len(self.avatars)
            result.extend([self.get_random_avatar() for _ in range(remaining)])
            return result

        return random.sample(self.avatars, count)

    def validate_avatar(self, avatar_path: str) -> bool:
        """
        Проверка аватарки на соответствие требованиям Steam

        Args:
            avatar_path: Путь к файлу аватарки

        Returns:
            True если аватарка валидна
        """
        if not os.path.exists(avatar_path):
            logger.error(f"✗ Файл не найден: {avatar_path}")
            return False

        try:
            with Image.open(avatar_path) as img:
                # Проверяем размер
                if img.size[0] > self.MAX_SIZE[0] or img.size[1] > self.MAX_SIZE[1]:
                    logger.warning(f"⚠ Аватарка {avatar_path} превышает максимальный размер")
                    return True  # Steam автоматически изменит размер

                return True

        except Exception as e:
            logger.error(f"✗ Ошибка валидации аватарки {avatar_path}: {str(e)}")
            return False

    def resize_avatar(self, avatar_path: str, output_path: str = None) -> str:
        """
        Изменение размера аватарки под требования Steam

        Args:
            avatar_path: Путь к исходной аватарке
            output_path: Путь для сохранения (если None, перезаписывает исходный файл)

        Returns:
            Путь к обработанной аватарке
        """
        try:
            with Image.open(avatar_path) as img:
                # Изменяем размер с сохранением пропорций
                img.thumbnail(self.MAX_SIZE, Image.Resampling.LANCZOS)

                # Сохраняем
                save_path = output_path if output_path else avatar_path
                img.save(save_path, quality=95)

                logger.info(f"✓ Аватарка изменена: {save_path}")
                return save_path

        except Exception as e:
            logger.error(f"✗ Ошибка изменения размера аватарки: {str(e)}")
            return avatar_path

    def get_avatar_count(self) -> int:
        """Получение количества доступных аватарок"""
        return len(self.avatars)
