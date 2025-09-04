import json
import os
from typing import Optional, List
from .nutrition_base import NutritionLookupProvider, NutritionInfo, NutritionResult


class TableNutritionProvider(NutritionLookupProvider):
    """Провайдер питательной ценности на основе JSON таблицы"""
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            # Путь к файлу данных относительно текущего файла
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(current_dir, "..", "..", "data", "nutrition_table.json")
        
        self.data_file = data_file
        self._load_data()
    
    def _load_data(self):
        """Загружает данные из JSON файла"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл данных не найден: {self.data_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {e}")
    
    async def get_nutrition_info(self, dish_name: str) -> Optional[NutritionInfo]:
        """
        Получает информацию о питательной ценности блюда
        """
        dish_name_lower = dish_name.lower().strip()
        
        # Прямой поиск
        if dish_name_lower in self.data["dishes"]:
            dish_data = self.data["dishes"][dish_name_lower]
            return NutritionInfo(
                kcal_per_100g=dish_data["kcal_per_100g"],
                protein=dish_data["protein"],
                fat=dish_data["fat"],
                carbs=dish_data["carbs"],
                notes=dish_data.get("notes", "")
            )
        
        # Поиск по частичному совпадению
        for dish_key, dish_data in self.data["dishes"].items():
            if dish_name_lower in dish_key or dish_key in dish_name_lower:
                return NutritionInfo(
                    kcal_per_100g=dish_data["kcal_per_100g"],
                    protein=dish_data["protein"],
                    fat=dish_data["fat"],
                    carbs=dish_data["carbs"],
                    notes=dish_data.get("notes", "")
                )
        
        return None
    
    async def calculate_nutrition(
        self, 
        dish_name: str, 
        weight_g: int, 
        cooking_method: str = "варка"
    ) -> Optional[NutritionResult]:
        """
        Рассчитывает питательную ценности для указанного веса и способа приготовления
        """
        nutrition_info = await self.get_nutrition_info(dish_name)
        if not nutrition_info:
            return None
        
        # Получаем множитель для способа приготовления
        cooking_multiplier = self.data["cooking_methods_multipliers"].get(
            cooking_method.lower(), 1.0
        )
        
        # Рассчитываем общие значения с учетом веса и способа приготовления
        weight_multiplier = weight_g / 100.0
        adjusted_kcal = nutrition_info.kcal_per_100g * cooking_multiplier * weight_multiplier
        
        total_protein = nutrition_info.protein * weight_multiplier
        total_fat = nutrition_info.fat * weight_multiplier
        total_carbs = nutrition_info.carbs * weight_multiplier
        
        # Формируем список допущений
        assumptions = []
        if cooking_method != "варка":
            assumptions.append(f"Учтено увеличение калорийности при {cooking_method}")
        if weight_g != 100:
            assumptions.append(f"Расчет для {weight_g}г (стандарт: 100г)")
        
        return NutritionResult(
            dish_name=dish_name,
            weight_g=weight_g,
            cooking_method=cooking_method,
            nutrition=nutrition_info,
            total_kcal=round(adjusted_kcal, 1),
            total_protein=round(total_protein, 1),
            total_fat=round(total_fat, 1),
            total_carbs=round(total_carbs, 1),
            confidence=0.8,
            assumptions=assumptions
        )


