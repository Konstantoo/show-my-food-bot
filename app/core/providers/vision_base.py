from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel


class VisionResult(BaseModel):
    """Результат анализа изображения"""
    label: str
    confidence: float
    description: str = ""


class VisionLabelProvider(ABC):
    """Базовый класс для провайдеров анализа изображений"""
    
    @abstractmethod
    async def analyze_image(self, image_data: bytes) -> List[VisionResult]:
        """
        Анализирует изображение и возвращает список возможных блюд
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Список результатов анализа с метками и уверенностью
        """
        pass
    
    @abstractmethod
    async def get_dish_suggestions(self, image_data: bytes) -> List[str]:
        """
        Получает предложения блюд на основе изображения
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Список названий блюд
        """
        pass


