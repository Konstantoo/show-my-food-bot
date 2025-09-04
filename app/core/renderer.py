from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List
from io import BytesIO
import os
from app.config import Config
from .providers.nutrition_base import NutritionResult
from .providers.fact_base import Fact


class CardRenderer:
    """Рендерер карточек блюд 16:9"""
    
    def __init__(self):
        self.card_width = Config.CARD_WIDTH
        self.card_height = Config.CARD_HEIGHT
        
        # Цвета
        self.colors = {
            'background': (248, 249, 250),  # Светло-серый
            'primary': (33, 37, 41),        # Темно-серый
            'secondary': (108, 117, 125),   # Серый
            'accent': (0, 123, 255),        # Синий
            'success': (40, 167, 69),       # Зеленый
            'warning': (255, 193, 7),       # Желтый
            'white': (255, 255, 255),
            'light_gray': (233, 236, 239)
        }
        
        # Загружаем шрифты
        self._load_fonts()
    
    def _load_fonts(self):
        """Загружает шрифты для рендеринга"""
        try:
            # Пытаемся загрузить системные шрифты
            self.title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            self.subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            self.body_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            self.small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        except:
            # Fallback на стандартный шрифт
            self.title_font = ImageFont.load_default()
            self.subtitle_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
    
    def render_card(
        self, 
        nutrition_result: NutritionResult, 
        facts: List[Fact] = None
    ) -> bytes:
        """
        Рендерит карточку блюда в формате PNG
        """
        # Создаем изображение
        img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Рендерим основные элементы
        self._render_header(draw, nutrition_result)
        self._render_nutrition_info(draw, nutrition_result)
        self._render_cooking_info(draw, nutrition_result)
        
        # Рендерим факты если есть
        if facts:
            self._render_facts(draw, facts)
        
        # Конвертируем в байты
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def _render_header(self, draw: ImageDraw.Draw, nutrition_result: NutritionResult):
        """Рендерит заголовок карточки"""
        # Название блюда
        dish_name = nutrition_result.dish_name.title()
        title_bbox = draw.textbbox((0, 0), dish_name, font=self.title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_width - title_width) // 2
        title_y = 40
        
        draw.text((title_x, title_y), dish_name, font=self.title_font, fill=self.colors['primary'])
        
        # Вес и калории
        weight_text = f"~{nutrition_result.total_kcal:.0f} ккал ({nutrition_result.weight_g}г)"
        weight_bbox = draw.textbbox((0, 0), weight_text, font=self.subtitle_font)
        weight_width = weight_bbox[2] - weight_bbox[0]
        weight_x = (self.card_width - weight_width) // 2
        weight_y = title_y + 70
        
        draw.text((weight_x, weight_y), weight_text, font=self.subtitle_font, fill=self.colors['accent'])
    
    def _render_nutrition_info(self, draw: ImageDraw.Draw, nutrition_result: NutritionResult):
        """Рендерит информацию о БЖУ"""
        # Фон для БЖУ
        bju_y = 180
        bju_height = 80
        bju_rect = (50, bju_y, self.card_width - 50, bju_y + bju_height)
        draw.rounded_rectangle(bju_rect, radius=10, fill=self.colors['white'])
        
        # Заголовок БЖУ
        bju_title = "Пищевая ценность (на порцию)"
        title_bbox = draw.textbbox((0, 0), bju_title, font=self.body_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_width - title_width) // 2
        draw.text((title_x, bju_y + 10), bju_title, font=self.body_font, fill=self.colors['secondary'])
        
        # Значения БЖУ
        bju_values = [
            f"Белки: {nutrition_result.total_protein:.1f}г",
            f"Жиры: {nutrition_result.total_fat:.1f}г", 
            f"Углеводы: {nutrition_result.total_carbs:.1f}г"
        ]
        
        bju_start_y = bju_y + 40
        for i, value in enumerate(bju_values):
            x = 100 + i * 300
            draw.text((x, bju_start_y), value, font=self.body_font, fill=self.colors['primary'])
    
    def _render_cooking_info(self, draw: ImageDraw.Draw, nutrition_result: NutritionResult):
        """Рендерит информацию о способе приготовления"""
        cooking_y = 300
        
        # Способ приготовления
        cooking_text = f"Способ: {nutrition_result.cooking_method.title()}"
        draw.text((50, cooking_y), cooking_text, font=self.body_font, fill=self.colors['primary'])
        
        # Допущения если есть
        if nutrition_result.assumptions:
            assumptions_text = " • ".join(nutrition_result.assumptions)
            draw.text((50, cooking_y + 35), assumptions_text, font=self.small_font, fill=self.colors['secondary'])
    
    def _render_facts(self, draw: ImageDraw.Draw, facts: List[Fact]):
        """Рендерит блок с фактами"""
        if not facts:
            return
        
        fact = facts[0]  # Берем первый факт
        
        # Фон для факта
        fact_y = 400
        fact_height = 120
        fact_rect = (50, fact_y, self.card_width - 50, fact_y + fact_height)
        draw.rounded_rectangle(fact_rect, radius=10, fill=self.colors['light_gray'])
        
        # Иконка факта
        fact_icon = "💡"
        draw.text((70, fact_y + 15), fact_icon, font=self.body_font)
        
        # Тип факта
        fact_type_map = {
            'history': 'История',
            'ingredient': 'Ингредиент', 
            'event': 'Событие',
            'celebrity': 'Знаменитость'
        }
        fact_type_text = fact_type_map.get(fact.type, 'Факт')
        draw.text((100, fact_y + 15), fact_type_text, font=self.small_font, fill=self.colors['accent'])
        
        # Текст факта
        fact_text = fact.text
        # Обрезаем текст если слишком длинный
        if len(fact_text) > 120:
            fact_text = fact_text[:117] + "..."
        
        # Разбиваем на строки если нужно
        lines = self._wrap_text(fact_text, self.card_width - 120, self.small_font)
        for i, line in enumerate(lines[:3]):  # Максимум 3 строки
            draw.text((70, fact_y + 45 + i * 20), line, font=self.small_font, fill=self.colors['primary'])
        
        # Источники
        if fact.sources:
            source_text = "Источник: " + self._get_domain_names(fact.sources)
            draw.text((70, fact_y + 100), source_text, font=self.small_font, fill=self.colors['secondary'])
    
    def _wrap_text(self, text: str, max_width: int, font) -> List[str]:
        """Разбивает текст на строки по ширине"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_domain_names(self, urls: List[str]) -> str:
        """Извлекает доменные имена из URL"""
        domains = []
        for url in urls:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain:
                    domains.append(domain)
            except:
                continue
        
        return ", ".join(domains[:2])  # Максимум 2 домена


