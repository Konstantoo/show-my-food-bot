import base64
import json
import random
from typing import List, Optional
from PIL import Image
from io import BytesIO
import aiohttp

from app.config import Config
from .quotes_provider import QuotesProvider


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
        self.quotes_provider = QuotesProvider()
        
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
        # Проверяем, есть ли валидный API ключ
        if not self.openai_api_key or self.openai_api_key == "your_openai_api_key_here" or len(self.openai_api_key) < 50:
            print("OpenAI API ключ не настроен, используем локальный анализ")
            return None
            
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
            
            timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд таймаут
            async with aiohttp.ClientSession(timeout=timeout) as session:
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
                        except json.JSONDecodeError as e:
                            print(f"Ошибка парсинга JSON от OpenAI: {e}")
                            return None
                    elif response.status == 403:
                        print("OpenAI API: Доступ запрещен (проверьте API ключ и биллинг)")
                        return None
                    elif response.status == 429:
                        print("OpenAI API: Превышен лимит запросов")
                        return None
                    else:
                        error_text = await response.text()
                        print(f"OpenAI API error {response.status}: {error_text}")
                        return None
                        
        except aiohttp.ClientError as e:
            print(f"Ошибка соединения с OpenAI API: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка OpenAI API: {e}")
            return None
    
    def _analyze_locally(self, image_info: dict) -> PhotoAnalysisResult:
        """Улучшенный локальный анализ фотографии"""
        # Анализируем аспектное соотношение
        aspect_ratio = image_info.get('aspect_ratio', 1.0)
        width = image_info.get('width', 1920)
        height = image_info.get('height', 1080)
        
        # Более детальный анализ композиции
        composition_tips = []
        lighting_tips = []
        technical_tips = []
        
        # Анализ по аспектному соотношению
        if aspect_ratio > 1.8:  # Очень широкое
            main_advice = "Панорамное фото! Используйте ведущие линии для направления взгляда зрителя через кадр."
            composition_tips.extend([
                "Размещайте важные объекты на пересечениях правила третей",
                "Используйте передний план для создания глубины"
            ])
        elif aspect_ratio > 1.3:  # Широкоформатное
            main_advice = "Хорошее широкоформатное фото! Экспериментируйте с горизонтальными линиями и симметрией."
            composition_tips.extend([
                "Попробуйте правило третей для размещения горизонта",
                "Используйте диагональные линии для динамики"
            ])
        elif aspect_ratio < 0.7:  # Портретное
            main_advice = "Отличная портретная ориентация! Обратите внимание на вертикальные линии и баланс."
            composition_tips.extend([
                "Размещайте главный объект не в центре кадра",
                "Используйте вертикальные элементы для усиления композиции"
            ])
        else:  # Квадратное или близкое к нему
            main_advice = "Сбалансированная композиция! Попробуйте центрированное размещение или симметрию."
            composition_tips.extend([
                "Экспериментируйте с симметричной композицией",
                "Используйте центральное размещение для статичных сцен"
            ])
        
        # Анализ разрешения
        total_pixels = width * height
        if total_pixels < 1000000:  # Меньше 1MP
            technical_tips.append("Попробуйте снимать в более высоком разрешении для лучшего качества")
        elif total_pixels > 10000000:  # Больше 10MP
            technical_tips.append("Отличное разрешение! Используйте его для детальных снимков")
        
        # Генерируем реалистичные оценки
        base_composition = 7
        base_lighting = 7  
        base_technical = 7
        
        # Модификаторы на основе характеристик
        if aspect_ratio in [1.0, 1.33, 1.5, 0.75]:  # Стандартные соотношения
            base_composition += 1
            
        if total_pixels > 5000000:  # Хорошее разрешение
            base_technical += 1
        elif total_pixels < 500000:  # Низкое разрешение
            base_technical -= 1
            
        # Добавляем случайность
        composition_score = max(1, min(10, base_composition + random.randint(-1, 2)))
        lighting_score = max(1, min(10, base_lighting + random.randint(-1, 2)))
        technical_score = max(1, min(10, base_technical + random.randint(-1, 1)))
        overall_score = (composition_score + lighting_score + technical_score) // 3
        
        # Собираем все советы
        all_advice = composition_tips + lighting_tips + technical_tips
        
        # Добавляем общие советы
        general_advice = random.sample(
            self.advice_database['composition'] + 
            self.advice_database['lighting'] + 
            self.advice_database['technical'],
            random.randint(1, 2)
        )
        all_advice.extend(general_advice)
        
        # Ограничиваем количество советов
        additional_advice = all_advice[:4]
        
        # Определяем настроение на основе соотношения сторон
        if aspect_ratio > 1.5:
            moods = ['панорамное', 'широкое', 'просторное', 'открытое']
        elif aspect_ratio < 0.8:
            moods = ['интимное', 'вертикальное', 'динамичное', 'элегантное']
        else:
            moods = ['сбалансированное', 'гармоничное', 'стабильное', 'классическое']
        
        mood = random.choice(moods)
        
        # Предложения по стилю на основе анализа
        if aspect_ratio > 1.5:
            style_base = ["пейзажная фотография", "архитектурная съемка", "панорамы"]
        elif aspect_ratio < 0.8:
            style_base = ["портретная фотография", "стрит-фотография", "модная съемка"]
        else:
            style_base = ["минимализм", "симметрия", "геометрия"]
            
        style_suggestions = random.sample(style_base + self.style_advice[:2], min(3, len(style_base) + 2))
        
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
    
    async def get_inspirational_quote(self, analysis_result, context: str = "") -> Optional[dict]:
        """Получает вдохновляющую цитату мастера фотографии"""
        try:
            quote = await self.quotes_provider.get_relevant_quote(analysis_result, context)
            if quote:
                return {
                    "text": quote.text,
                    "author": quote.author,
                    "profession": quote.profession,
                    "context": quote.context,
                    "relevance": quote.relevance_score
                }
        except Exception as e:
            print(f"Ошибка получения цитаты: {e}")
        
        return None
    
    async def get_multiple_quotes(self, analysis_result, count: int = 2) -> List[dict]:
        """Получает несколько релевантных цитат"""
        try:
            quotes = await self.quotes_provider.get_multiple_quotes(analysis_result, count)
            return [
                {
                    "text": quote.text,
                    "author": quote.author,
                    "profession": quote.profession,
                    "context": quote.context,
                    "relevance": quote.relevance_score
                }
                for quote in quotes
            ]
        except Exception as e:
            print(f"Ошибка получения цитат: {e}")
            return []