from typing import List, Optional, Tuple
from .providers.vision_base import VisionLabelProvider, VisionResult
from .providers.nutrition_base import NutritionLookupProvider, NutritionResult
from .providers.fact_base import FactProvider, FactResult
from .providers.vision_dummy import DummyVisionProvider
from .providers.nutrition_table import TableNutritionProvider
from .providers.hybrid_fact import HybridFactProvider


class DishAnalyzer:
    """Анализатор блюд - координирует работу всех провайдеров"""
    
    def __init__(
        self,
        vision_provider: VisionLabelProvider = None,
        nutrition_provider: NutritionLookupProvider = None,
        fact_provider: FactProvider = None
    ):
        self.vision_provider = vision_provider or DummyVisionProvider()
        self.nutrition_provider = nutrition_provider or TableNutritionProvider()
        self.fact_provider = fact_provider or HybridFactProvider()
    
    async def analyze_image(self, image_data: bytes) -> List[VisionResult]:
        """
        Анализирует изображение и возвращает возможные блюда
        """
        try:
            results = await self.vision_provider.analyze_image(image_data)
            return results
        except Exception as e:
            print(f"Ошибка анализа изображения: {e}")
            return []
    
    async def get_dish_suggestions(self, image_data: bytes) -> List[str]:
        """
        Получает предложения блюд на основе изображения
        """
        try:
            suggestions = await self.vision_provider.get_dish_suggestions(image_data)
            return suggestions
        except Exception as e:
            print(f"Ошибка получения предложений блюд: {e}")
            return []
    
    async def calculate_nutrition(
        self, 
        dish_name: str, 
        weight_g: int, 
        cooking_method: str = "варка"
    ) -> Optional[NutritionResult]:
        """
        Рассчитывает питательную ценность блюда
        """
        try:
            result = await self.nutrition_provider.calculate_nutrition(
                dish_name, weight_g, cooking_method
            )
            return result
        except Exception as e:
            print(f"Ошибка расчета питательной ценности: {e}")
            return None
    
    async def get_facts(
        self, 
        dish_name: str, 
        ingredients: List[str] = None,
        exclude_facts: List[str] = None
    ) -> FactResult:
        """
        Получает факты о блюде
        """
        try:
            result = await self.fact_provider.get_facts(
                dish_name, ingredients, exclude_facts
            )
            return result
        except Exception as e:
            print(f"Ошибка получения фактов: {e}")
            return FactResult(facts=[], total_found=0)
    
    async def get_fallback_facts(self, exclude_facts: List[str] = None) -> List:
        """
        Получает резервные факты
        """
        try:
            facts = await self.fact_provider.get_fallback_facts(exclude_facts)
            return facts
        except Exception as e:
            print(f"Ошибка получения резервных фактов: {e}")
            return []
    
    async def get_ingredients_for_dish(self, dish_name: str) -> List[str]:
        """
        Получает список ингредиентов для блюда (если доступно)
        """
        try:
            # Пытаемся получить информацию о блюде из nutrition provider
            nutrition_info = await self.nutrition_provider.get_nutrition_info(dish_name)
            if nutrition_info and hasattr(nutrition_info, 'ingredients'):
                return nutrition_info.ingredients
        except Exception as e:
            print(f"Ошибка получения ингредиентов: {e}")
        
        return []
    
    async def full_analysis(
        self, 
        dish_name: str, 
        weight_g: int, 
        cooking_method: str = "варка",
        exclude_facts: List[str] = None
    ) -> Tuple[Optional[NutritionResult], FactResult]:
        """
        Выполняет полный анализ блюда: питательная ценность + факты
        """
        # Получаем ингредиенты для более точного поиска фактов
        ingredients = await self.get_ingredients_for_dish(dish_name)
        
        # Параллельно получаем питательную ценность и факты
        nutrition_task = self.calculate_nutrition(dish_name, weight_g, cooking_method)
        facts_task = self.get_facts(dish_name, ingredients, exclude_facts)
        
        nutrition_result = await nutrition_task
        facts_result = await facts_task
        
        # Если нет специфичных фактов, получаем резервные
        if not facts_result.facts:
            fallback_facts = await self.get_fallback_facts(exclude_facts)
            facts_result.facts = fallback_facts
            facts_result.total_found = len(fallback_facts)
        
        return nutrition_result, facts_result


