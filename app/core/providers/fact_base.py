from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Fact(BaseModel):
    """Факт о блюде"""
    type: str  # history, ingredient, event, celebrity
    text: str
    sources: List[str]
    verified: bool
    confidence: float


class FactResult(BaseModel):
    """Результат поиска фактов"""
    facts: List[Fact]
    total_found: int
    filtered_celebrity: int = 0


class FactProvider(ABC):
    """Базовый класс для провайдеров фактов"""
    
    @abstractmethod
    async def get_facts(
        self, 
        dish_name: str, 
        ingredients: List[str] = None,
        exclude_facts: List[str] = None
    ) -> FactResult:
        """
        Получает факты о блюде
        
        Args:
            dish_name: Название блюда
            ingredients: Список ингредиентов
            exclude_facts: Список текстов фактов для исключения
            
        Returns:
            Результат поиска фактов
        """
        pass
    
    @abstractmethod
    async def get_fallback_facts(self, exclude_facts: List[str] = None) -> List[Fact]:
        """
        Получает резервные факты, если нет специфичных для блюда
        
        Args:
            exclude_facts: Список текстов фактов для исключения
            
        Returns:
            Список резервных фактов
        """
        pass


