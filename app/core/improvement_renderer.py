from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List


class ImprovementRenderer:
    """Рендерер схем улучшения фотографий еды"""
    
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
            'warning': '#F39C12',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'border': '#BDC3C7',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2'
        }
    
    def render_improvement_card(self, analysis_data: Dict) -> bytes:
        """Создает карточку с анализом и рекомендациями по улучшению"""
        try:
            # Создаем изображение
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Градиентный фон
            self._draw_gradient_background(draw)
            
            # Заголовок
            self._draw_header(draw, "📸 Анализ фотографии еды")
            
            # Анализ композиции
            self._draw_composition_analysis(draw, analysis_data)
            
            # Рекомендации
            self._draw_recommendations(draw, analysis_data.get('recommendations', []))
            
            # Жанр
            self._draw_genre_info(draw, analysis_data.get('genre', {}))
            
            # Подвал
            self._draw_footer(draw)
            
            # Сохраняем в байты
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG', quality=95)
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"Ошибка создания карточки улучшения: {e}")
            return self._create_simple_card(analysis_data)
    
    def _draw_gradient_background(self, draw):
        """Рисует градиентный фон"""
        for y in range(self.card_height):
            ratio = y / self.card_height
            r = int(102 + (118 - 102) * ratio)
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            color = (r, g, b)
            draw.line([(0, y), (self.card_width, y)], fill=color)
    
    def _draw_header(self, draw, title):
        """Рисует заголовок"""
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Заголовок
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_width - title_width) // 2
        title_y = 30
        
        # Тень
        draw.text((title_x + 2, title_y + 2), title, font=title_font, fill=(0, 0, 0, 100))
        draw.text((title_x, title_y), title, font=title_font, fill=self.colors['background'])
        
        # Подзаголовок
        subtitle_text = "🎯 Рекомендации по улучшению"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.card_width - subtitle_width) // 2
        subtitle_y = title_y + 60
        
        draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=self.colors['background'])
    
    def _draw_composition_analysis(self, draw, analysis_data):
        """Рисует анализ композиции"""
        try:
            info_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            value_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 22)
        except:
            info_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
        
        # Позиция
        start_y = 150
        left_margin = 50
        right_margin = self.card_width - 50
        
        # Фон для анализа
        analysis_bg_height = 120
        draw.rounded_rectangle(
            [left_margin - 15, start_y - 15, right_margin + 15, start_y + analysis_bg_height],
            radius=12,
            fill=(255, 255, 255, 200)
        )
        
        # Заголовок анализа
        draw.text((left_margin, start_y), "📊 Анализ композиции:", font=value_font, fill=self.colors['primary'])
        
        # Элементы анализа
        analysis = analysis_data.get('analysis', {})
        technical = analysis_data.get('technical', {})
        
        elements = [
            ("🎨 Цвета:", analysis.get('colors', 'Не определено')),
            ("💡 Освещение:", analysis.get('lighting', 'Не определено')),
            ("📐 Композиция:", analysis.get('composition', 'Не определено')),
            ("📱 Разрешение:", technical.get('resolution', 'Не определено'))
        ]
        
        for i, (label, value) in enumerate(elements):
            y = start_y + 35 + i * 20
            draw.text((left_margin, y), label, font=info_font, fill=self.colors['text_primary'])
            
            # Обрезаем длинные значения
            if len(value) > 40:
                value = value[:37] + "..."
            
            draw.text((left_margin + 120, y), value, font=info_font, fill=self.colors['text_secondary'])
    
    def _draw_recommendations(self, draw, recommendations):
        """Рисует рекомендации"""
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 24)
            rec_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            rec_font = ImageFont.load_default()
        
        # Позиция
        start_y = 300
        left_margin = 50
        right_margin = self.card_width - 50
        
        # Заголовок
        draw.text((left_margin, start_y), "💡 Рекомендации по улучшению:", font=title_font, fill=self.colors['primary'])
        
        # Рекомендации
        for i, rec in enumerate(recommendations[:4]):  # Максимум 4 рекомендации
            y = start_y + 35 + i * 25
            
            # Фон для рекомендации
            draw.rounded_rectangle(
                [left_margin - 10, y - 5, right_margin + 10, y + 20],
                radius=8,
                fill=(255, 255, 255, 150)
            )
            
            # Текст рекомендации
            if len(rec) > 60:
                rec = rec[:57] + "..."
            draw.text((left_margin, y), rec, font=rec_font, fill=self.colors['text_primary'])
    
    def _draw_genre_info(self, draw, genre_data):
        """Рисует информацию о жанре"""
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 20)
            info_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Позиция
        start_y = 500
        left_margin = 50
        right_margin = self.card_width - 50
        
        if genre_data.get('detected_genre') != 'unknown':
            genre_info = genre_data.get('genre_info', {})
            genre_name = genre_info.get('name', 'Неизвестный жанр')
            genre_desc = genre_info.get('description', '')
            
            # Фон для жанра
            draw.rounded_rectangle(
                [left_margin - 10, start_y - 10, right_margin + 10, start_y + 80],
                radius=10,
                fill=(255, 255, 255, 180)
            )
            
            # Название жанра
            draw.text((left_margin, start_y), f"🎭 Жанр: {genre_name}", font=title_font, fill=self.colors['secondary'])
            
            # Описание жанра
            if len(genre_desc) > 80:
                genre_desc = genre_desc[:77] + "..."
            draw.text((left_margin, start_y + 25), genre_desc, font=info_font, fill=self.colors['text_secondary'])
            
            # Уверенность
            confidence = genre_data.get('confidence', 0)
            conf_text = f"Уверенность: {int(confidence * 100)}%"
            draw.text((left_margin, start_y + 50), conf_text, font=info_font, fill=self.colors['success'])
    
    def _draw_footer(self, draw):
        """Рисует подвал"""
        try:
            footer_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            footer_font = ImageFont.load_default()
        
        footer_text = "📸 Food Photo Analyzer • Улучшите свои фотографии еды!"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.card_width - footer_width) // 2
        footer_y = self.card_height - 30
        
        draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=self.colors['text_secondary'])
    
    def _create_simple_card(self, analysis_data):
        """Создает простую карточку в случае ошибки"""
        try:
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            text = "📸 Анализ фотографии еды\n\n"
            text += "Рекомендации:\n"
            for rec in analysis_data.get('recommendations', [])[:3]:
                text += f"• {rec}\n"
            
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
