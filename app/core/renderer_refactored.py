from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional
class CardRendererRefactored:
    """Улучшенный рендерер карточек с красивым дизайном"""
    
    def __init__(self):
        self.card_width = 1280
        self.card_height = 720
        
        # Цветовая схема
        self.colors = {
            'background': '#FFFFFF',
            'primary': '#2C3E50',
            'secondary': '#3498DB',
            'accent': '#E74C3C',
            'success': '#27AE60',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'border': '#BDC3C7',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2'
        }
    
    def render_card(self, nutrition_result, facts: List = None) -> bytes:
        """Создает красивую карточку с информацией о блюде"""
        try:
            # Создаем изображение
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Создаем градиентный фон
            self._draw_gradient_background(draw)
            
            # Заголовок
            self._draw_header(draw, nutrition_result.dish_name.title())
            
            # Основная информация
            self._draw_nutrition_info(draw, nutrition_result)
            
            # Факт (если есть)
            if facts and len(facts) > 0:
                self._draw_fact(draw, facts[0])
            
            # Подвал
            self._draw_footer(draw)
            
            # Сохраняем в байты
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG', quality=95)
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"Ошибка создания карточки: {e}")
            # Возвращаем простую карточку в случае ошибки
            return self._create_simple_card(nutrition_result)
    
    def _draw_gradient_background(self, draw):
        """Рисует градиентный фон"""
        for y in range(self.card_height):
            # Создаем градиент от синего к фиолетовому
            ratio = y / self.card_height
            r = int(102 + (118 - 102) * ratio)  # 667eea -> 764ba2
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            
            color = (r, g, b)
            draw.line([(0, y), (self.card_width, y)], fill=color)
    
    def _draw_header(self, draw, dish_name):
        """Рисует заголовок карточки"""
        try:
            # Загружаем шрифт (пробуем разные пути)
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/ArialHB.ttc",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ]
            
            title_font = None
            subtitle_font = None
            
            for font_path in font_paths:
                try:
                    title_font = ImageFont.truetype(font_path, 48)
                    subtitle_font = ImageFont.truetype(font_path, 24)
                    break
                except:
                    continue
            
            if not title_font:
                raise Exception("No font found")
                
        except:
            # Fallback шрифты
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Заголовок
        title_bbox = draw.textbbox((0, 0), dish_name, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_width - title_width) // 2
        title_y = 40
        
        # Тень для заголовка
        draw.text((title_x + 2, title_y + 2), dish_name, font=title_font, fill=(0, 0, 0, 100))
        draw.text((title_x, title_y), dish_name, font=title_font, fill=self.colors['background'])
        
        # Подзаголовок
        subtitle_text = "🍽️ Анализ питательной ценности"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.card_width - subtitle_width) // 2
        subtitle_y = title_y + 60
        
        draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=self.colors['background'])
    
    def _draw_nutrition_info(self, draw, nutrition_result):
        """Рисует информацию о питательной ценности"""
        try:
            # Загружаем шрифты (пробуем разные пути)
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/ArialHB.ttc",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ]
            
            info_font = None
            value_font = None
            small_font = None
            
            for font_path in font_paths:
                try:
                    info_font = ImageFont.truetype(font_path, 32)
                    value_font = ImageFont.truetype(font_path, 36)
                    small_font = ImageFont.truetype(font_path, 20)
                    break
                except:
                    continue
            
            if not info_font:
                raise Exception("No font found")
                
        except:
            info_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Позиция начала
        start_y = 180
        line_height = 50
        left_margin = 80
        right_margin = self.card_width - 80
        
        # Фон для информации
        info_bg_height = 200
        draw.rounded_rectangle(
            [left_margin - 20, start_y - 20, right_margin + 20, start_y + info_bg_height],
            radius=15,
            fill=(255, 255, 255, 200)
        )
        
        # Основные показатели
        metrics = [
            ("🔥", "Калории", f"{nutrition_result.total_kcal} ккал", self.colors['accent']),
            ("🥩", "Белки", f"{nutrition_result.total_protein}г", self.colors['success']),
            ("🥓", "Жиры", f"{nutrition_result.total_fat}г", self.colors['secondary']),
            ("🍞", "Углеводы", f"{nutrition_result.total_carbs}г", self.colors['primary'])
        ]
        
        for i, (emoji, label, value, color) in enumerate(metrics):
            y = start_y + i * line_height
            
            # Эмодзи
            draw.text((left_margin, y), emoji, font=info_font, fill=color)
            
            # Название
            draw.text((left_margin + 50, y + 5), label, font=info_font, fill=self.colors['text_primary'])
            
            # Значение
            value_bbox = draw.textbbox((0, 0), value, font=value_font)
            value_width = value_bbox[2] - value_bbox[0]
            value_x = right_margin - value_width
            draw.text((value_x, y), value, font=value_font, fill=color)
        
        # Дополнительная информация
        details_y = start_y + info_bg_height + 20
        details_text = f"⚖️ Вес: {nutrition_result.weight_g}г  |  👨‍🍳 {nutrition_result.cooking_method}"
        details_bbox = draw.textbbox((0, 0), details_text, font=small_font)
        details_width = details_bbox[2] - details_bbox[0]
        details_x = (self.card_width - details_width) // 2
        draw.text((details_x, details_y), details_text, font=small_font, fill=self.colors['text_secondary'])
    
    def _draw_fact(self, draw, fact):
        """Рисует интересный факт"""
        try:
            # Загружаем шрифты (пробуем разные пути)
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/ArialHB.ttc",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ]
            
            fact_font = None
            title_font = None
            
            for font_path in font_paths:
                try:
                    fact_font = ImageFont.truetype(font_path, 24)
                    title_font = ImageFont.truetype(font_path, 28)
                    break
                except:
                    continue
            
            if not fact_font:
                raise Exception("No font found")
                
        except:
            fact_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Позиция
        fact_y = 420
        left_margin = 60
        right_margin = self.card_width - 60
        
        # Фон для факта
        fact_bg_height = 120
        draw.rounded_rectangle(
            [left_margin - 15, fact_y - 15, right_margin + 15, fact_y + fact_bg_height],
            radius=12,
            fill=(255, 255, 255, 180)
        )
        
        # Заголовок факта
        fact_title = f"💡 {fact.type.title()}"
        draw.text((left_margin, fact_y), fact_title, font=title_font, fill=self.colors['primary'])
        
        # Текст факта (обрезаем если слишком длинный)
        fact_text = fact.text
        if len(fact_text) > 200:
            fact_text = fact_text[:200] + "..."
        
        # Разбиваем текст на строки
        words = fact_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=fact_font)
            if bbox[2] - bbox[0] < right_margin - left_margin:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Рисуем строки
        for i, line in enumerate(lines[:3]):  # Максимум 3 строки
            y = fact_y + 35 + i * 25
            draw.text((left_margin, y), line, font=fact_font, fill=self.colors['text_primary'])
    
    def _draw_footer(self, draw):
        """Рисует подвал карточки"""
        try:
            # Загружаем шрифт (пробуем разные пути)
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/ArialHB.ttc",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ]
            
            footer_font = None
            
            for font_path in font_paths:
                try:
                    footer_font = ImageFont.truetype(font_path, 18)
                    break
                except:
                    continue
            
            if not footer_font:
                raise Exception("No font found")
                
        except:
            footer_font = ImageFont.load_default()
        
        footer_text = "🍽️ Show My Food Bot • Анализ питательной ценности"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.card_width - footer_width) // 2
        footer_y = self.card_height - 40
        
        draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=self.colors['text_secondary'])
    
    def _create_simple_card(self, nutrition_result) -> bytes:
        """Создает простую карточку в случае ошибки"""
        try:
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Простой текст
            text = f"{nutrition_result.dish_name.title()}\n"
            text += f"Калории: {nutrition_result.total_kcal} ккал\n"
            text += f"Белки: {nutrition_result.total_protein}г\n"
            text += f"Жиры: {nutrition_result.total_fat}г\n"
            text += f"Углеводы: {nutrition_result.total_carbs}г"
            
            draw.text((50, 50), text, fill=self.colors['text_primary'])
            
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
        except:
            # В крайнем случае возвращаем пустое изображение
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return img_byte_arr.getvalue()
