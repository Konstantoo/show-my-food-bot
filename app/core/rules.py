from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.config import Config


@dataclass
class ValidationRule:
    """Правило валидации"""
    name: str
    description: str
    validator: callable
    error_message: str


class ValidationRules:
    """Набор правил валидации для бота"""
    
    @staticmethod
    def validate_dish_name(name: str) -> bool:
        """Проверяет валидность названия блюда"""
        if not name or not name.strip():
            return False
        
        # Минимальная и максимальная длина
        if len(name.strip()) < 2 or len(name.strip()) > 100:
            return False
        
        # Проверяем на недопустимые символы
        forbidden_chars = ['<', '>', '&', '"', "'", '\\', '/', '\n', '\r', '\t']
        if any(char in name for char in forbidden_chars):
            return False
        
        return True
    
    @staticmethod
    def validate_weight(weight: int) -> bool:
        """Проверяет валидность веса"""
        return 1 <= weight <= 5000  # От 1г до 5кг
    
    @staticmethod
    def validate_cooking_method(method: str) -> bool:
        """Проверяет валидность способа приготовления"""
        valid_methods = [
            'варка', 'жарка', 'запекание', 'тушение', 'гриль', 
            'жарка на углях', 'сырой', 'запеченная', 'жареная',
            'тушеная', 'вареный', 'варенная'
        ]
        return method.lower() in valid_methods
    
    @staticmethod
    def validate_image_size(data: bytes) -> bool:
        """Проверяет размер изображения"""
        max_size_mb = 20.0
        size_mb = len(data) / (1024 * 1024)
        return size_mb <= max_size_mb
    
    @staticmethod
    def validate_fact_text(text: str) -> bool:
        """Проверяет валидность текста факта"""
        if not text or not text.strip():
            return False
        
        # Минимальная и максимальная длина
        if len(text.strip()) < 10 or len(text.strip()) > 500:
            return False
        
        return True
    
    @staticmethod
    def validate_sources(sources: List[str]) -> bool:
        """Проверяет валидность списка источников"""
        if not sources or not isinstance(sources, list):
            return False
        
        # Проверяем каждый источник
        for source in sources:
            if not isinstance(source, str) or not source.strip():
                return False
            
            # Проверяем, что это URL
            if not source.startswith(('http://', 'https://')):
                return False
        
        return True


class BusinessRules:
    """Бизнес-правила для работы бота"""
    
    # Максимальное количество фактов на блюдо
    MAX_FACTS_PER_DISH = Config.MAX_FACTS_PER_DISH
    
    # Максимальное количество резервных фактов
    MAX_FALLBACK_FACTS = Config.MAX_FALLBACK_FACTS
    
    # Минимальная уверенность для показа фактов
    MIN_FACT_CONFIDENCE = 0.3
    
    # Требования для celebrity фактов
    MIN_CELEBRITY_SOURCES = 2
    
    @staticmethod
    def should_show_celebrity_fact(fact) -> bool:
        """Определяет, нужно ли показывать celebrity факт"""
        if fact.type != 'celebrity':
            return True
        
        # Для celebrity фактов требуем верификацию и минимум 2 источника
        return (fact.verified and 
                len(fact.sources) >= BusinessRules.MIN_CELEBRITY_SOURCES and
                fact.confidence >= BusinessRules.MIN_FACT_CONFIDENCE)
    
    @staticmethod
    def filter_facts_by_confidence(facts: List, min_confidence: float = None) -> List:
        """Фильтрует факты по минимальной уверенности"""
        if min_confidence is None:
            min_confidence = BusinessRules.MIN_FACT_CONFIDENCE
        
        return [fact for fact in facts if fact.confidence >= min_confidence]
    
    @staticmethod
    def prioritize_facts(facts: List) -> List:
        """Сортирует факты по приоритету"""
        # Приоритет: verified факты, затем по confidence
        return sorted(facts, key=lambda x: (x.verified, x.confidence), reverse=True)
    
    @staticmethod
    def limit_facts_count(facts: List, max_count: int = None) -> List:
        """Ограничивает количество фактов"""
        if max_count is None:
            max_count = BusinessRules.MAX_FACTS_PER_DISH
        
        return facts[:max_count]
    
    @staticmethod
    def get_cooking_method_multiplier(method: str) -> float:
        """Возвращает множитель калорийности для способа приготовления"""
        multipliers = {
            'сырой': 1.0,
            'варка': 1.0,
            'тушение': 1.1,
            'жарка': 1.2,
            'запекание': 1.15,
            'гриль': 1.2,
            'жарка на углях': 1.25,
            'запеченная': 1.15,
            'жареная': 1.2,
            'тушеная': 1.1,
            'вареный': 1.0,
            'варенная': 1.0
        }
        
        return multipliers.get(method.lower(), 1.0)
    
    @staticmethod
    def get_default_weight_for_dish(dish_name: str) -> int:
        """Возвращает дефолтный вес для блюда"""
        # Дефолтные веса для разных типов блюд
        defaults = {
            'суп': 300,
            'салат': 200,
            'паста': 250,
            'пицца': 200,
            'борщ': 300,
            'плов': 250,
            'блины': 150,
            'пельмени': 200,
            'оладьи': 150,
            'шашлык': 200
        }
        
        dish_lower = dish_name.lower()
        for key, weight in defaults.items():
            if key in dish_lower:
                return weight
        
        return 200  # Дефолтный вес


