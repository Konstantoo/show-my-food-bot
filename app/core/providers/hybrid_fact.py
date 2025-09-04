import json
import os
import random
from typing import List, Optional
from .fact_base import FactProvider, Fact, FactResult
from .perplexity_fact import PerplexityFactProvider


class HybridFactProvider(FactProvider):
    """Гибридный провайдер фактов: локальная таблица + Perplexity API"""
    
    def __init__(self, data_file: str = None, use_perplexity: bool = True):
        # Загружаем локальную таблицу фактов
        if data_file is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(current_dir, "..", "..", "data", "facts_table.json")
        
        self.data_file = data_file
        self.use_perplexity = use_perplexity
        self._load_local_data()
        
        # Инициализируем Perplexity провайдер если нужно
        if self.use_perplexity:
            try:
                self.perplexity_provider = PerplexityFactProvider()
            except ValueError:
                print("Perplexity API недоступен, используем только локальные факты")
                self.use_perplexity = False
                self.perplexity_provider = None
    
    def _load_local_data(self):
        """Загружает локальные факты из JSON файла"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"Файл фактов не найден: {self.data_file}")
            self.data = {"facts": [], "fallback_facts": []}
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON фактов: {e}")
            self.data = {"facts": [], "fallback_facts": []}
    
    async def get_facts(
        self, 
        dish_name: str, 
        ingredients: List[str] = None,
        exclude_facts: List[str] = None
    ) -> FactResult:
        """
        Получает факты о блюде из локальной таблицы и Perplexity
        """
        exclude_facts = exclude_facts or []
        all_facts = []
        filtered_celebrity = 0
        
        # 1. Получаем факты из локальной таблицы
        local_facts = self._get_local_facts(dish_name, ingredients, exclude_facts)
        all_facts.extend(local_facts)
        
        # 2. Получаем факты из Perplexity (если доступен)
        if self.use_perplexity and self.perplexity_provider:
            try:
                perplexity_result = await self.perplexity_provider.get_facts(
                    dish_name, ingredients, exclude_facts
                )
                all_facts.extend(perplexity_result.facts)
                filtered_celebrity += perplexity_result.filtered_celebrity
            except Exception as e:
                print(f"Ошибка получения фактов из Perplexity: {e}")
        
        # 3. Фильтруем дубликаты и нежелательные факты
        unique_facts = self._filter_unique_facts(all_facts, exclude_facts)
        
        # 4. Сортируем по приоритету (verified факты первыми)
        unique_facts.sort(key=lambda x: (x.verified, x.confidence), reverse=True)
        
        return FactResult(
            facts=unique_facts[:3],  # Максимум 3 факта
            total_found=len(all_facts),
            filtered_celebrity=filtered_celebrity
        )
    
    def _get_local_facts(
        self, 
        dish_name: str, 
        ingredients: List[str] = None,
        exclude_facts: List[str] = None
    ) -> List[Fact]:
        """Получает факты из локальной таблицы"""
        facts = []
        dish_name_lower = dish_name.lower().strip()
        ingredients_lower = [ing.lower().strip() for ing in (ingredients or [])]
        
        for fact_group in self.data.get("facts", []):
            match = fact_group.get("match", {})
            
            # Проверяем совпадение по названию блюда
            dish_match = False
            for fact_dish in match.get("dish_names", []):
                if (dish_name_lower == fact_dish.lower() or 
                    dish_name_lower in fact_dish.lower() or 
                    fact_dish.lower() in dish_name_lower):
                    dish_match = True
                    break
            
            # Проверяем совпадение по ингредиентам
            ingredient_match = False
            if ingredients_lower:
                fact_ingredients = [ing.lower() for ing in match.get("ingredients", [])]
                common_ingredients = set(ingredients_lower) & set(fact_ingredients)
                if len(common_ingredients) >= 2:  # Минимум 2 общих ингредиента
                    ingredient_match = True
            
            # Если есть совпадение, добавляем факты
            if dish_match or ingredient_match:
                for fact_data in fact_group.get("facts", []):
                    if fact_data.get("text", "") not in (exclude_facts or []):
                        facts.append(Fact(
                            type=fact_data.get("type", "history"),
                            text=fact_data.get("text", ""),
                            sources=fact_data.get("sources", []),
                            verified=fact_data.get("verified", True),
                            confidence=fact_data.get("confidence", 0.8)
                        ))
        
        return facts
    
    def _filter_unique_facts(self, facts: List[Fact], exclude_facts: List[str]) -> List[Fact]:
        """Фильтрует дубликаты и исключенные факты"""
        seen_texts = set(exclude_facts or [])
        unique_facts = []
        
        for fact in facts:
            if fact.text not in seen_texts:
                seen_texts.add(fact.text)
                unique_facts.append(fact)
        
        return unique_facts
    
    async def get_fallback_facts(self, exclude_facts: List[str] = None) -> List[Fact]:
        """
        Получает резервные факты
        """
        exclude_facts = exclude_facts or []
        all_facts = []
        
        # 1. Локальные резервные факты
        local_fallback = self.data.get("fallback_facts", [])
        for fact_data in local_fallback:
            if fact_data.get("text", "") not in exclude_facts:
                all_facts.append(Fact(
                    type=fact_data.get("type", "ingredient"),
                    text=fact_data.get("text", ""),
                    sources=fact_data.get("sources", []),
                    verified=fact_data.get("verified", True),
                    confidence=fact_data.get("confidence", 0.8)
                ))
        
        # 2. Резервные факты из Perplexity
        if self.use_perplexity and self.perplexity_provider:
            try:
                perplexity_fallback = await self.perplexity_provider.get_fallback_facts(exclude_facts)
                all_facts.extend(perplexity_fallback)
            except Exception as e:
                print(f"Ошибка получения резервных фактов из Perplexity: {e}")
        
        # Фильтруем дубликаты
        unique_facts = self._filter_unique_facts(all_facts, exclude_facts)
        
        # Возвращаем случайные факты
        if len(unique_facts) > 2:
            return random.sample(unique_facts, 2)
        return unique_facts


