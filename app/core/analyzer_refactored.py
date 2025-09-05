import random
import re
from typing import List, Optional, Tuple
from .providers.nutrition_base import NutritionLookupProvider, NutritionResult
from .providers.fact_base import FactProvider, FactResult
from .providers.nutrition_table import TableNutritionProvider
from .providers.hybrid_fact import HybridFactProvider
from .providers.openai_vision import OpenAIVisionProvider
from app.config import Config


class DishAnalyzerRefactored:
    """Улучшенный анализатор блюд с лучшим распознаванием"""
    
    def __init__(
        self,
        nutrition_provider: NutritionLookupProvider = None,
        fact_provider: FactProvider = None,
        vision_provider = None
    ):
        self.nutrition_provider = nutrition_provider or TableNutritionProvider()
        self.fact_provider = fact_provider or HybridFactProvider()
        
        # Инициализируем OpenAI Vision API если есть ключ
        if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != "your_openai_api_key_here":
            self.vision_provider = vision_provider or OpenAIVisionProvider(Config.OPENAI_API_KEY)
        else:
            # Fallback на заглушку если нет ключа
            from .providers.vision_dummy import DummyVisionProvider
            self.vision_provider = vision_provider or DummyVisionProvider()
        
        # Расширенный список блюд для распознавания
        self.dish_database = {
            # Паста и макароны
            "паста": ["паста", "макароны", "спагетти", "лапша", "фетучини", "пенне"],
            "паста карбонара": ["карбонара", "паста карбонара", "карбонара паста"],
            "паста болоньезе": ["болоньезе", "паста болоньезе", "спагетти болоньезе"],
            "лазанья": ["лазанья", "лазания"],
            
            # Супы
            "борщ": ["борщ", "борщ украинский", "красный борщ"],
            "щи": ["щи", "щи капустные"],
            "солянка": ["солянка", "солянка мясная"],
            "харчо": ["харчо", "суп харчо"],
            "том ям": ["том ям", "том ям кунг"],
            
            # Мясные блюда
            "плов": ["плов", "плов узбекский", "плов с мясом"],
            "шашлык": ["шашлык", "шашлык из свинины", "шашлык из курицы"],
            "котлеты": ["котлеты", "котлеты мясные", "котлеты по-киевски"],
            "пельмени": ["пельмени", "пельмешки"],
            "манты": ["манты", "манты с мясом"],
            
            # Салаты
            "салат цезарь": ["цезарь", "салат цезарь", "цезарь салат"],
            "оливье": ["оливье", "салат оливье", "оливье салат"],
            "греческий салат": ["греческий", "греческий салат", "салат греческий"],
            "винегрет": ["винегрет", "винегрет салат"],
            
            # Пицца
            "пицца маргарита": ["маргарита", "пицца маргарита", "маргарита пицца"],
            "пицца пепперони": ["пепперони", "пицца пепперони", "пепперони пицца"],
            "пицца": ["пицца", "пицца с сыром"],
            
            # Азиатская кухня
            "суши": ["суши", "роллы", "суши роллы"],
            "рамен": ["рамен", "рамен суп"],
            "пад тай": ["пад тай", "пат тай"],
            "курица терияки": ["терияки", "курица терияки", "терияки курица"],
            
            # Десерты
            "блины": ["блины", "блинчики", "блины с начинкой"],
            "оладьи": ["оладьи", "оладушки"],
            "сырники": ["сырники", "творожники"],
            "торт": ["торт", "тортик", "торт с кремом"],
            
            # Завтраки
            "омлет": ["омлет", "яичница", "глазунья"],
            "каша": ["каша", "овсянка", "гречка", "рисовая каша"],
            "тосты": ["тосты", "тост с маслом"],
            
            # Напитки
            "кофе": ["кофе", "кофе с молоком", "латте", "капучино"],
            "чай": ["чай", "черный чай", "зеленый чай"],
        }
    
    async def get_dish_suggestions(self, image_data: bytes) -> List[str]:
        """
        Получает предложения блюд на основе изображения
        Использует OpenAI Vision API для реального анализа
        """
        try:
            # Используем реальный анализ изображения через OpenAI
            suggestions = await self.vision_provider.get_dish_suggestions(image_data)
            return suggestions
        except Exception as e:
            print(f"Ошибка получения предложений блюд: {e}")
            # Fallback на заглушку в случае ошибки
            return self._simulate_image_analysis()
    
    def _simulate_image_analysis(self) -> List[str]:
        """Имитирует анализ изображения с более умными результатами"""
        # Выбираем случайную категорию блюд
        categories = list(self.dish_database.keys())
        selected_category = random.choice(categories)
        
        # Получаем варианты из этой категории
        variants = self.dish_database[selected_category]
        
        # Возвращаем 1-3 варианта
        num_suggestions = random.randint(1, min(3, len(variants)))
        return random.sample(variants, num_suggestions)
    
    async def calculate_nutrition(
        self, 
        dish_name: str, 
        weight_g: int, 
        cooking_method: str = "варка"
    ) -> Optional[NutritionResult]:
        """
        Рассчитывает питательную ценность блюда с улучшенным поиском
        """
        try:
            # Нормализуем название блюда
            normalized_name = self._normalize_dish_name(dish_name)
            
            result = await self.nutrition_provider.calculate_nutrition(
                normalized_name, weight_g, cooking_method
            )
            return result
        except Exception as e:
            print(f"Ошибка расчета питательной ценности: {e}")
            return None
    
    def _normalize_dish_name(self, dish_name: str) -> str:
        """Нормализует название блюда для поиска в базе"""
        dish_name = dish_name.lower().strip()
        
        # Убираем лишние слова
        dish_name = re.sub(r'\s+(г|грамм|кг|килограмм)\b', '', dish_name)
        dish_name = re.sub(r'\s+(жареный|жареная|жареное|варёный|вареный|варенная|варенное)\b', '', dish_name)
        
        # Ищем точное совпадение в базе
        for base_name, variants in self.dish_database.items():
            if dish_name in variants or any(variant in dish_name for variant in variants):
                return base_name
        
        # Если не найдено, возвращаем как есть
        return dish_name
    
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
            # Нормализуем название для поиска фактов
            normalized_name = self._normalize_dish_name(dish_name)
            
            result = await self.fact_provider.get_facts(
                normalized_name, ingredients, exclude_facts
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
        Получает список ингредиентов для блюда
        """
        try:
            normalized_name = self._normalize_dish_name(dish_name)
            nutrition_info = await self.nutrition_provider.get_nutrition_info(normalized_name)
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
