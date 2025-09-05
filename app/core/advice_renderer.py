from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List


class AdviceRenderer:
    """Рендерер карточек с советами по фотографии"""
    
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
    
    def render_advice_card(self, analysis_result) -> bytes:
        """Создает красивую карточку с советами по фотографии"""
        try:
            # Создаем изображение
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Создаем градиентный фон
            self._draw_gradient_background(draw)
            
            # Заголовок
            self._draw_header(draw, "📸 Анализ фотографии")
            
            # Основная информация
            self._draw_scores(draw, analysis_result)
            
            # Главный совет
            self._draw_main_advice(draw, analysis_result.main_advice)
            
            # Дополнительные советы
            if analysis_result.additional_advice:
                self._draw_additional_advice(draw, analysis_result.additional_advice)
            
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
            return self._create_simple_card(analysis_result)
    
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
    
    def _draw_header(self, draw, title):
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
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_width - title_width) // 2
        title_y = 40
        
        # Тень для заголовка
        draw.text((title_x + 2, title_y + 2), title, font=title_font, fill=(0, 0, 0, 100))
        draw.text((title_x, title_y), title, font=title_font, fill=self.colors['background'])
        
        # Подзаголовок
        subtitle_text = "💡 Советы по улучшению"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.card_width - subtitle_width) // 2
        subtitle_y = title_y + 60
        
        draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=self.colors['background'])
    
    def _draw_scores(self, draw, analysis_result):
        """Рисует оценки по разным критериям"""
        try:
            score_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            label_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            score_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        # Позиция начала
        start_y = 150
        line_height = 50
        left_margin = 80
        right_margin = self.card_width - 80
        
        # Фон для оценок
        score_bg_height = 200
        draw.rounded_rectangle(
            [left_margin - 20, start_y - 20, right_margin + 20, start_y + score_bg_height],
            radius=15,
            fill=(255, 255, 255, 200)
        )
        
        # Оценки
        scores = [
            ("📐", "Композиция", analysis_result.composition_score, self.colors['primary']),
            ("💡", "Освещение", analysis_result.lighting_score, self.colors['warning']),
            ("⚙️", "Техника", analysis_result.technical_score, self.colors['success']),
            ("⭐", "Общая", analysis_result.overall_score, self.colors['accent'])
        ]
        
        for i, (emoji, label, score, color) in enumerate(scores):
            y = start_y + i * line_height
            
            # Эмодзи
            draw.text((left_margin, y), emoji, font=score_font, fill=color)
            
            # Название
            draw.text((left_margin + 50, y + 5), label, font=label_font, fill=self.colors['text_primary'])
            
            # Оценка
            score_text = f"{score}/10"
            score_bbox = draw.textbbox((0, 0), score_text, font=score_font)
            score_width = score_bbox[2] - score_bbox[0]
            score_x = right_margin - score_width
            draw.text((score_x, y), score_text, font=score_font, fill=color)
            
            # Прогресс-бар
            bar_width = 200
            bar_height = 8
            bar_x = right_margin - bar_width - 80
            bar_y = y + 15
            
            # Фон прогресс-бара
            draw.rounded_rectangle(
                [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                radius=4,
                fill=self.colors['border']
            )
            
            # Заполнение прогресс-бара
            fill_width = int((score / 10) * bar_width)
            if fill_width > 0:
                draw.rounded_rectangle(
                    [bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
                    radius=4,
                    fill=color
                )
    
    def _draw_main_advice(self, draw, main_advice):
        """Рисует главный совет"""
        try:
            advice_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 28)
        except:
            advice_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Позиция
        advice_y = 380
        left_margin = 60
        right_margin = self.card_width - 60
        
        # Фон для совета
        advice_bg_height = 120
        draw.rounded_rectangle(
            [left_margin - 15, advice_y - 15, right_margin + 15, advice_y + advice_bg_height],
            radius=12,
            fill=(255, 255, 255, 180)
        )
        
        # Заголовок совета
        advice_title = "💡 Главный совет"
        draw.text((left_margin, advice_y), advice_title, font=title_font, fill=self.colors['primary'])
        
        # Текст совета (обрезаем если слишком длинный)
        advice_text = main_advice
        if len(advice_text) > 150:
            advice_text = advice_text[:150] + "..."
        
        # Разбиваем текст на строки
        words = advice_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=advice_font)
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
            y = advice_y + 35 + i * 25
            draw.text((left_margin, y), line, font=advice_font, fill=self.colors['text_primary'])
    
    def _draw_additional_advice(self, draw, additional_advice):
        """Рисует дополнительные советы"""
        try:
            advice_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 24)
        except:
            advice_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Позиция
        advice_y = 520
        left_margin = 60
        right_margin = self.card_width - 60
        
        # Заголовок
        advice_title = "🔧 Дополнительные советы"
        draw.text((left_margin, advice_y), advice_title, font=title_font, fill=self.colors['primary'])
        
        # Советы (максимум 2)
        for i, advice in enumerate(additional_advice[:2]):
            y = advice_y + 30 + i * 25
            bullet_text = f"• {advice}"
            
            # Обрезаем если слишком длинный
            if len(bullet_text) > 80:
                bullet_text = bullet_text[:80] + "..."
            
            draw.text((left_margin, y), bullet_text, font=advice_font, fill=self.colors['text_primary'])
    
    def _draw_footer(self, draw):
        """Рисует подвал карточки"""
        try:
            footer_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        except:
            footer_font = ImageFont.load_default()
        
        footer_text = "📸 Photo Advice Bot • Советы по фотографии"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.card_width - footer_width) // 2
        footer_y = self.card_height - 40
        
        draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=self.colors['text_secondary'])
    
    def _create_simple_card(self, analysis_result) -> bytes:
        """Создает простую карточку в случае ошибки"""
        try:
            img = Image.new('RGB', (self.card_width, self.card_height), self.colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Простой текст
            text = f"📸 Анализ фотографии\n\n"
            text += f"Композиция: {analysis_result.composition_score}/10\n"
            text += f"Освещение: {analysis_result.lighting_score}/10\n"
            text += f"Техника: {analysis_result.technical_score}/10\n"
            text += f"Общая оценка: {analysis_result.overall_score}/10\n\n"
            text += f"Совет: {analysis_result.main_advice}"
            
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
