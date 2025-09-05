from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List


class ModernPhotoRenderer:
    """Современный рендерер схем улучшения фотографий"""
    
    def __init__(self):
        self.card_width = 1280
        self.card_height = 720
        
        # Современная цветовая схема
        self.colors = {
            'background': '#FFFFFF',
            'primary': '#1a1a1a',      # Темно-серый
            'secondary': '#6366f1',     # Индиго
            'accent': '#f59e0b',        # Янтарный
            'success': '#10b981',       # Изумрудный
            'warning': '#f97316',       # Оранжевый
            'error': '#ef4444',         # Красный
            'text_primary': '#1f2937',  # Темно-серый
            'text_secondary': '#6b7280', # Средне-серый
            'text_light': '#9ca3af',    # Светло-серый
            'border': '#e5e7eb',        # Светло-серый
            'gradient_start': '#667eea', # Синий
            'gradient_end': '#764ba2',   # Фиолетовый
            'card_bg': '#f8fafc',       # Очень светло-серый
            'highlight': '#fef3c7'      # Светло-желтый
        }
    
    def render_photo_analysis_card(self, analysis_data: Dict) -> bytes:
        """Создает современную карточку с анализом фотографии"""
        try:
            # Создаем изображение
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Градиентный фон
            self._draw_modern_gradient(draw)
            
            # Заголовок
            self._draw_modern_header(draw)
            
            # Основной анализ
            self._draw_main_analysis(draw, analysis_data)
            
            # Рекомендации
            self._draw_recommendations_section(draw, analysis_data.get('recommendations', []))
            
            # Тип фотографии
            self._draw_photo_type_section(draw, analysis_data.get('photo_type', {}))
            
            # Подвал
            self._draw_modern_footer(draw)
            
            # Сохраняем в байты
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG', quality=95)
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"Ошибка создания карточки: {e}")
            return self._create_fallback_card(analysis_data)
    
    def _draw_modern_gradient(self, draw):
        """Рисует современный градиентный фон"""
        for y in range(self.card_height):
            ratio = y / self.card_height
            # Создаем более мягкий градиент
            r = int(102 + (118 - 102) * ratio)
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            # Добавляем прозрачность
            alpha = int(0.1 * 255)
            color = (r, g, b, alpha)
            draw.line([(0, y), (self.card_width, y)], fill=(r, g, b))
    
    def _draw_modern_header(self, draw):
        """Рисует современный заголовок"""
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 52)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Главный заголовок
        title = "📸 Photo Analyzer"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_width - title_width) // 2
        title_y = 40
        
        # Тень для заголовка
        draw.text((title_x + 3, title_y + 3), title, font=title_font, fill=(0, 0, 0, 50))
        draw.text((title_x, title_y), title, font=title_font, fill=self.colors['primary'])
        
        # Подзаголовок
        subtitle = "✨ Анализ и рекомендации по улучшению"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.card_width - subtitle_width) // 2
        subtitle_y = title_y + 70
        
        draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=self.colors['text_secondary'])
    
    def _draw_main_analysis(self, draw, analysis_data):
        """Рисует основной анализ"""
        try:
            info_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            value_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 22)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            info_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Позиция
        start_y = 150
        left_margin = 60
        right_margin = self.card_width - 60
        
        # Фон для анализа
        analysis_bg_height = 140
        draw.rounded_rectangle(
            [left_margin - 20, start_y - 20, right_margin + 20, start_y + analysis_bg_height],
            radius=16,
            fill=self.colors['card_bg']
        )
        
        # Заголовок секции
        draw.text((left_margin, start_y), "🔍 Анализ фотографии", font=value_font, fill=self.colors['primary'])
        
        # Элементы анализа
        analysis = analysis_data.get('analysis', {})
        technical = analysis_data.get('technical', {})
        
        # Первая строка
        elements_row1 = [
            ("🎨 Цвета:", analysis.get('colors', 'Не определено')[:25] + "..." if len(analysis.get('colors', '')) > 25 else analysis.get('colors', 'Не определено')),
            ("💡 Освещение:", analysis.get('lighting', 'Не определено')[:25] + "..." if len(analysis.get('lighting', '')) > 25 else analysis.get('lighting', 'Не определено'))
        ]
        
        for i, (label, value) in enumerate(elements_row1):
            x = left_margin + i * (right_margin - left_margin) // 2
            y = start_y + 35
            draw.text((x, y), label, font=info_font, fill=self.colors['text_primary'])
            draw.text((x, y + 25), value, font=small_font, fill=self.colors['text_secondary'])
        
        # Вторая строка
        elements_row2 = [
            ("📐 Композиция:", analysis.get('composition', 'Не определено')[:25] + "..." if len(analysis.get('composition', '')) > 25 else analysis.get('composition', 'Не определено')),
            ("📱 Разрешение:", technical.get('resolution', 'Не определено'))
        ]
        
        for i, (label, value) in enumerate(elements_row2):
            x = left_margin + i * (right_margin - left_margin) // 2
            y = start_y + 85
            draw.text((x, y), label, font=info_font, fill=self.colors['text_primary'])
            draw.text((x, y + 25), value, font=small_font, fill=self.colors['text_secondary'])
    
    def _draw_recommendations_section(self, draw, recommendations):
        """Рисует секцию рекомендаций"""
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 24)
            rec_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            rec_font = ImageFont.load_default()
        
        # Позиция
        start_y = 320
        left_margin = 60
        right_margin = self.card_width - 60
        
        # Заголовок
        draw.text((left_margin, start_y), "💡 Рекомендации по улучшению", font=title_font, fill=self.colors['primary'])
        
        # Рекомендации в две колонки
        for i, rec in enumerate(recommendations[:4]):  # Максимум 4 рекомендации
            col = i % 2
            row = i // 2
            
            x = left_margin + col * (right_margin - left_margin) // 2
            y = start_y + 40 + row * 35
            
            # Фон для рекомендации
            draw.rounded_rectangle(
                [x - 10, y - 8, x + (right_margin - left_margin) // 2 - 20, y + 25],
                radius=8,
                fill=self.colors['highlight']
            )
            
            # Текст рекомендации
            if len(rec) > 35:
                rec = rec[:32] + "..."
            draw.text((x, y), rec, font=rec_font, fill=self.colors['text_primary'])
    
    def _draw_photo_type_section(self, draw, photo_type_data):
        """Рисует секцию типа фотографии"""
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 20)
            info_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Позиция
        start_y = 500
        left_margin = 60
        right_margin = self.card_width - 60
        
        if photo_type_data.get('detected_type') != 'unknown':
            type_info = photo_type_data.get('type_info', {})
            type_name = type_info.get('name', 'Неизвестный тип')
            type_desc = type_info.get('description', '')
            confidence = photo_type_data.get('confidence', 0)
            
            # Фон для типа
            draw.rounded_rectangle(
                [left_margin - 15, start_y - 15, right_margin + 15, start_y + 100],
                radius=12,
                fill=self.colors['card_bg']
            )
            
            # Название типа
            draw.text((left_margin, start_y), f"🎭 Тип: {type_name}", font=title_font, fill=self.colors['secondary'])
            
            # Описание типа
            if len(type_desc) > 60:
                type_desc = type_desc[:57] + "..."
            draw.text((left_margin, start_y + 30), type_desc, font=info_font, fill=self.colors['text_secondary'])
            
            # Уверенность
            conf_text = f"Уверенность: {int(confidence * 100)}%"
            draw.text((left_margin, start_y + 55), conf_text, font=info_font, fill=self.colors['success'])
    
    def _draw_modern_footer(self, draw):
        """Рисует современный подвал"""
        try:
            footer_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        except:
            footer_font = ImageFont.load_default()
        
        footer_text = "📸 Photo Analyzer • Улучшите свои фотографии с помощью ИИ"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.card_width - footer_width) // 2
        footer_y = self.card_height - 40
        
        draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=self.colors['text_light'])
    
    def _create_fallback_card(self, analysis_data):
        """Создает простую карточку в случае ошибки"""
        try:
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            text = "📸 Анализ фотографии\n\n"
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
