import re
import validators
from typing import List, Optional, Tuple


class TextParser:
    """Парсер текста для извлечения информации о блюдах"""
    
    @staticmethod
    def parse_dish_description(text: str) -> Tuple[str, Optional[int], str]:
        """
        Парсит описание блюда и извлекает название, вес и способ приготовления
        
        Примеры:
        - "паста карбонара 250г запеченная" -> ("паста карбонара", 250, "запеченная")
        - "борщ 300" -> ("борщ", 300, "варка")
        - "плов" -> ("плов", 100, "варка")
        """
        text = text.lower().strip()
        
        # Ищем вес в граммах
        weight_match = re.search(r'(\d+)\s*г', text)
        weight = int(weight_match.group(1)) if weight_match else None
        
        # Удаляем вес из текста для поиска названия
        if weight_match:
            text = text.replace(weight_match.group(0), '').strip()
        
        # Список способов приготовления
        cooking_methods = [
            'варка', 'жарка', 'запекание', 'тушение', 'гриль', 
            'жарка на углях', 'сырой', 'запеченная', 'жареная',
            'тушеная', 'вареный', 'варенная'
        ]
        
        # Ищем способ приготовления
        cooking_method = "варка"  # По умолчанию
        for method in cooking_methods:
            if method in text:
                cooking_method = method
                text = text.replace(method, '').strip()
                break
        
        # Очищаем название от лишних слов
        dish_name = re.sub(r'\s+', ' ', text).strip()
        
        # Если название пустое, возвращаем дефолтные значения
        if not dish_name:
            return ("неизвестное блюдо", weight or 100, cooking_method)
        
        return (dish_name, weight or 100, cooking_method)
    
    @staticmethod
    def extract_weight(text: str) -> Optional[int]:
        """Извлекает вес из текста"""
        weight_match = re.search(r'(\d+)\s*г', text.lower())
        return int(weight_match.group(1)) if weight_match else None
    
    @staticmethod
    def extract_cooking_method(text: str) -> str:
        """Извлекает способ приготовления из текста"""
        cooking_methods = [
            'варка', 'жарка', 'запекание', 'тушение', 'гриль', 
            'жарка на углях', 'сырой', 'запеченная', 'жареная',
            'тушеная', 'вареный', 'варенная'
        ]
        
        text_lower = text.lower()
        for method in cooking_methods:
            if method in text_lower:
                return method
        
        return "варка"  # По умолчанию
    
    @staticmethod
    def clean_dish_name(text: str) -> str:
        """Очищает название блюда от лишних слов"""
        # Удаляем вес и способы приготовления
        text = re.sub(r'\d+\s*г', '', text.lower())
        
        cooking_methods = [
            'варка', 'жарка', 'запекание', 'тушение', 'гриль', 
            'жарка на углях', 'сырой', 'запеченная', 'жареная',
            'тушеная', 'вареный', 'варенная'
        ]
        
        for method in cooking_methods:
            text = text.replace(method, '')
        
        # Удаляем лишние пробелы и знаки препинания
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Проверяет валидность URL"""
        return validators.url(url) is True
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Извлекает домен из URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return None
    
    @staticmethod
    def format_sources(sources: List[str], max_domains: int = 2) -> str:
        """Форматирует список источников для отображения"""
        if not sources:
            return ""
        
        domains = []
        for source in sources:
            domain = TextParser.extract_domain(source)
            if domain and domain not in domains:
                domains.append(domain)
                if len(domains) >= max_domains:
                    break
        
        return ", ".join(domains)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Обрезает текст до указанной длины"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    @staticmethod
    def format_nutrition_text(nutrition_result) -> str:
        """Форматирует текст с информацией о питательной ценности"""
        if not nutrition_result:
            return "Информация о питательной ценности недоступна"
        
        text = f"🍽️ {nutrition_result.dish_name.title()}\n\n"
        text += f"📊 Калории: ~{nutrition_result.total_kcal:.0f} ккал ({nutrition_result.weight_g}г)\n"
        text += f"🥩 Белки: {nutrition_result.total_protein:.1f}г\n"
        text += f"🥓 Жиры: {nutrition_result.total_fat:.1f}г\n"
        text += f"🍞 Углеводы: {nutrition_result.total_carbs:.1f}г\n"
        text += f"👨‍🍳 Способ: {nutrition_result.cooking_method.title()}\n"
        
        if nutrition_result.assumptions:
            text += f"\n⚠️ Допущения: {' • '.join(nutrition_result.assumptions)}"
        
        return text


