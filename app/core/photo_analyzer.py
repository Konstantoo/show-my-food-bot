import base64
import json
import random
from typing import List, Optional
from PIL import Image
from io import BytesIO
import aiohttp

from app.config import Config


class PhotoAnalysisResult:
    """Результат анализа фотографии"""
    
    def __init__(self, 
                 main_advice: str,
                 composition_score: int,
                 lighting_score: int,
                 technical_score: int,
                 overall_score: int,
                 additional_advice: List[str] = None,
                 mood: str = None,
                 style_suggestions: List[str] = None):
        self.main_advice = main_advice
        self.composition_score = composition_score
        self.lighting_score = lighting_score
        self.technical_score = technical_score
        self.overall_score = overall_score
        self.additional_advice = additional_advice or []
        self.mood = mood or "нейтральное"
        self.style_suggestions = style_suggestions or []


class PhotoAnalyzer:
    """Анализатор фотографий для предоставления советов"""
    
    def __init__(self):
        self.openai_api_key = Config.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        # База знаний советов по фотографии
        self.advice_database = {
            "composition": [
                "Используйте правило третей - размещайте важные элементы на пересечениях линий",
                "Создавайте глубину с помощью переднего, среднего и заднего планов",
                "Используйте ведущие линии для направления взгляда зрителя",
                "Экспериментируйте с симметрией для создания баланса",
                "Избегайте размещения главного объекта в центре кадра"
            ],
            "lighting": [
                "Снимайте в золотой час для мягкого теплого света",
                "Используйте рассеянный свет для портретов",
                "Экспериментируйте с контровым освещением",
                "Обращайте внимание на тени - они создают объем",
                "Используйте отражатели для заполнения теней"
            ],
            "technical": [
                "Проверьте резкость перед съемкой",
                "Используйте штатив для стабилизации камеры",
                "Настройте правильный баланс белого",
                "Экспериментируйте с глубиной резкости",
                "Снимайте в RAW для лучшего качества"
            ],
            "post_processing": [
                "Корректируйте экспозицию и контраст",
                "Настройте насыщенность и яркость цветов",
                "Используйте маски для локальной коррекции",
                "Применяйте шумоподавление при необходимости",
                "Экспериментируйте с черно-белым преобразованием"
            ]
        }
        
        # Советы по стилю
        self.style_advice = [
            "Создавайте серии фотографий в едином стиле",
            "Экспериментируйте с цветовыми палитрами",
            "Используйте минимализм для создания сильных образов",
            "Попробуйте разные жанры фотографии",
            "Развивайте свой уникальный стиль"
        ]
    
    async def analyze_photo(self, image_data: bytes) -> Optional[PhotoAnalysisResult]:
        """
        Анализирует фотографию и возвращает советы
        """
        try:
            # Получаем базовую информацию об изображении
            image_info = self._get_image_info(image_data)
            
            # Используем OpenAI для анализа если доступен
            if self.openai_api_key and self.openai_api_key != "your_openai_api_key_here":
                ai_analysis = await self._analyze_with_openai(image_data)
                if ai_analysis:
                    return ai_analysis
            
            # Fallback на локальный анализ
            return self._analyze_locally(image_info)
            
        except Exception as e:
            print(f"Ошибка анализа фото: {e}")
            return self._create_fallback_analysis()
    
    def _get_image_info(self, image_data: bytes) -> dict:
        """Получает базовую информацию об изображении"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'aspect_ratio': img.width / img.height
                }
        except Exception as e:
            print(f"Ошибка получения информации об изображении: {e}")
            return {'width': 1920, 'height': 1080, 'mode': 'RGB', 'format': 'JPEG', 'aspect_ratio': 16/9}
    
    async def _analyze_with_openai(self, image_data: bytes) -> Optional[PhotoAnalysisResult]:
        """Анализирует фото с помощью OpenAI Vision API"""
        try:
            # Кодируем изображение в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Проанализируй эту фотографию и дай советы по улучшению. 
                                Верни ответ в формате JSON с полями:
                                - main_advice: главный совет (строка)
                                - composition_score: оценка композиции (1-10)
                                - lighting_score: оценка освещения (1-10)
                                - technical_score: техническая оценка (1-10)
                                - overall_score: общая оценка (1-10)
                                - additional_advice: дополнительные советы (массив строк)
                                - mood: настроение фото (строка)
                                - style_suggestions: предложения по стилю (массив строк)
                                
                                Пример ответа:
                                {
                                    "main_advice": "Попробуйте использовать правило третей для лучшей композиции",
                                    "composition_score": 6,
                                    "lighting_score": 7,
                                    "technical_score": 8,
                                    "overall_score": 7,
                                    "additional_advice": ["Добавьте больше контраста", "Попробуйте другой угол"],
                                    "mood": "спокойное",
                                    "style_suggestions": ["минимализм", "черно-белое"]
                                }"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Парсим JSON ответ
                        try:
                            analysis_data = json.loads(content)
                            return PhotoAnalysisResult(
                                main_advice=analysis_data.get('main_advice', 'Хорошая фотография!'),
                                composition_score=analysis_data.get('composition_score', 7),
                                lighting_score=analysis_data.get('lighting_score', 7),
                                technical_score=analysis_data.get('technical_score', 7),
                                overall_score=analysis_data.get('overall_score', 7),
                                additional_advice=analysis_data.get('additional_advice', []),
                                mood=analysis_data.get('mood', 'нейтральное'),
                                style_suggestions=analysis_data.get('style_suggestions', [])
                            )
                        except json.JSONDecodeError:
                            return None
                    else:
                        print(f"OpenAI API error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Ошибка анализа через OpenAI: {e}")
            return None
    
    def _analyze_locally(self, image_info: dict) -> PhotoAnalysisResult:
        """Локальный анализ фотографии"""
        # Анализируем аспектное соотношение
        aspect_ratio = image_info['aspect_ratio']
        
        # Определяем основной совет на основе характеристик
        if aspect_ratio > 1.5:  # Широкоформатное
            main_advice = "Отличное широкоформатное фото! Попробуйте использовать правило третей для размещения объектов."
        elif aspect_ratio < 0.8:  # Портретное
            main_advice = "Хорошее портретное фото! Обратите внимание на освещение лица и фон."
        else:  # Квадратное или близкое к квадрату
            main_advice = "Интересная композиция! Экспериментируйте с симметрией и центрированием."
        
        # Генерируем случайные оценки (7-9 для хороших фото)
        composition_score = random.randint(6, 9)
        lighting_score = random.randint(6, 9)
        technical_score = random.randint(7, 9)
        overall_score = (composition_score + lighting_score + technical_score) // 3
        
        # Выбираем случайные дополнительные советы
        additional_advice = random.sample(
            self.advice_database['composition'] + 
            self.advice_database['lighting'] + 
            self.advice_database['technical'],
            random.randint(2, 4)
        )
        
        # Определяем настроение
        moods = ['спокойное', 'динамичное', 'романтичное', 'драматичное', 'минималистичное']
        mood = random.choice(moods)
        
        # Предложения по стилю
        style_suggestions = random.sample(self.style_advice, random.randint(1, 3))
        
        return PhotoAnalysisResult(
            main_advice=main_advice,
            composition_score=composition_score,
            lighting_score=lighting_score,
            technical_score=technical_score,
            overall_score=overall_score,
            additional_advice=additional_advice,
            mood=mood,
            style_suggestions=style_suggestions
        )
    
    def _create_fallback_analysis(self) -> PhotoAnalysisResult:
        """Создает резервный анализ в случае ошибки"""
        return PhotoAnalysisResult(
            main_advice="Хорошая фотография! Продолжайте экспериментировать с композицией и освещением.",
            composition_score=7,
            lighting_score=7,
            technical_score=7,
            overall_score=7,
            additional_advice=[
                "Попробуйте разные углы съемки",
                "Обратите внимание на освещение",
                "Экспериментируйте с композицией"
            ],
            mood="нейтральное",
            style_suggestions=["развивайте свой стиль"]
        )
    
    async def get_additional_advice(self, current_analysis: PhotoAnalysisResult) -> List[str]:
        """Получает дополнительные советы на основе текущего анализа"""
        # Выбираем советы, которые еще не показывались
        all_advice = (
            self.advice_database['composition'] + 
            self.advice_database['lighting'] + 
            self.advice_database['technical'] + 
            self.advice_database['post_processing']
        )
        
        # Фильтруем уже показанные советы
        available_advice = [advice for advice in all_advice 
                          if advice not in current_analysis.additional_advice]
        
        # Возвращаем случайные советы
        if available_advice:
            return random.sample(available_advice, min(3, len(available_advice)))
        else:
            return ["Продолжайте практиковаться и экспериментировать!"]