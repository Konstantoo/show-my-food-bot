from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class NutritionInfo(BaseModel):
    """Информация о питательной ценности"""
    kcal_per_100g: float
    protein: float  # граммы на 100г
    fat: float      # граммы на 100г
    carbs: float    # граммы на 100г
    notes: str = ""


class NutritionResult(BaseModel):
    """Результат расчета питательной ценности"""
    dish_name: str
    weight_g: int
    cooking_method: str
    nutrition: NutritionInfo
    total_kcal: float
    total_protein: float
    total_fat: float
    total_carbs: float
    confidence: float = 0.8
    assumptions: List[str] = []


class NutritionLookupProvider(ABC):
    """Базовый класс для провайдеров информации о питательной ценности"""
    
    @abstractmethod
    async def get_nutrition_info(self, dish_name: str) -> Optional[NutritionInfo]:
        """
        Получает информацию о питательной ценности блюда
        
        Args:
            dish_name: Название блюда
            
        Returns:
            Информация о питательной ценности или None
        """
        pass
    
    @abstractmethod
    async def calculate_nutrition(
        self, 
        dish_name: str, 
        weight_g: int, 
        cooking_method: str = "варка"
    ) -> Optional[NutritionResult]:
        """
        Рассчитывает питательную ценности для указанного веса и способа приготовления
        
        Args:
            dish_name: Название блюда
            weight_g: Вес в граммах
            cooking_method: Способ приготовления
            
        Returns:
            Результат расчета или None
        """
        pass


