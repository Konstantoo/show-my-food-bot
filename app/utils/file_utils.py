import os
import tempfile
from typing import Optional, Tuple
from PIL import Image
import aiohttp
from io import BytesIO


class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    async def download_image(url: str) -> Optional[bytes]:
        """Скачивает изображение по URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"Ошибка скачивания изображения: {e}")
        
        return None
    
    @staticmethod
    def validate_image(image_data: bytes) -> bool:
        """Проверяет, является ли данные валидным изображением"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_image_info(image_data: bytes) -> Optional[Tuple[int, int, str]]:
        """Получает информацию об изображении (ширина, высота, формат)"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                return (img.width, img.height, img.format)
        except Exception:
            return None
    
    @staticmethod
    def resize_image_if_needed(
        image_data: bytes, 
        max_width: int = 1920, 
        max_height: int = 1080,
        quality: int = 85
    ) -> bytes:
        """Изменяет размер изображения если оно слишком большое"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Проверяем размер
                if img.width <= max_width and img.height <= max_height:
                    return image_data
                
                # Вычисляем новые размеры с сохранением пропорций
                ratio = min(max_width / img.width, max_height / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                
                # Изменяем размер
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Сохраняем в байты
                buffer = BytesIO()
                resized_img.save(buffer, format='JPEG', quality=quality, optimize=True)
                return buffer.getvalue()
        
        except Exception as e:
            print(f"Ошибка изменения размера изображения: {e}")
            return image_data
    
    @staticmethod
    def create_temp_file(data: bytes, suffix: str = '.tmp') -> str:
        """Создает временный файл с данными"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(data)
            return temp_file.name
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Удаляет временный файл"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Ошибка удаления временного файла: {e}")
    
    @staticmethod
    def get_file_size_mb(data: bytes) -> float:
        """Возвращает размер файла в мегабайтах"""
        return len(data) / (1024 * 1024)
    
    @staticmethod
    def is_image_too_large(data: bytes, max_size_mb: float = 20.0) -> bool:
        """Проверяет, не слишком ли большое изображение"""
        return FileUtils.get_file_size_mb(data) > max_size_mb


