import random
from typing import List
from .vision_base import VisionLabelProvider, VisionResult


class DummyVisionProvider(VisionLabelProvider):
    """Заглушка для анализа изображений (для MVP)"""
    
    def __init__(self):
        # Список популярных блюд для случайного выбора
        self.dish_suggestions = [
            "паста карбонара",
            "борщ", 
            "плов",
            "салат цезарь",
            "пицца маргарита",
            "суши",
            "шашлык",
            "блины",
            "пельмени",
            "оладьи"
        ]
    
    async def analyze_image(self, image_data: bytes) -> List[VisionResult]:
        """
        Имитирует анализ изображения, возвращая случайные результаты
        """
        # Выбираем 1-3 случайных блюда
        num_suggestions = random.randint(1, 3)
        selected_dishes = random.sample(self.dish_suggestions, num_suggestions)
        
        results = []
        for i, dish in enumerate(selected_dishes):
            # Первое блюдо имеет самую высокую уверенность
            confidence = 0.9 - (i * 0.2)
            confidence = max(0.3, confidence)  # Минимум 30%
            
            results.append(VisionResult(
                label=dish,
                confidence=confidence,
                description=f"Возможно, это {dish}"
            ))
        
        return results
    
    async def get_dish_suggestions(self, image_data: bytes) -> List[str]:
        """
        Возвращает предложения блюд на основе анализа изображения
        """
        results = await self.analyze_image(image_data)
        return [result.label for result in results]


