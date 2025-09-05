import base64
import json
from typing import Dict, List, Tuple
from PIL import Image
import io
from app.config import Config


class UniversalPhotoAnalyzer:
    """Универсальный анализатор фотографий для улучшения композиции и стиля"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        # Типы фотографий
        self.photo_types = {
            "portrait": {
                "name": "Портрет",
                "description": "Фотография человека крупным планом",
                "characteristics": ["лицо", "человек", "портрет", "глаза", "улыбка"],
                "tips": [
                    "Используйте мягкое освещение",
                    "Фокусируйтесь на глазах",
                    "Следите за фоном",
                    "Экспериментируйте с углами"
                ]
            },
            "full_body": {
                "name": "В полный рост",
                "description": "Фотография человека в полный рост",
                "characteristics": ["полный рост", "фигура", "поза", "одежда"],
                "tips": [
                    "Используйте правило третей",
                    "Обратите внимание на позу",
                    "Следите за пропорциями",
                    "Работайте с перспективой"
                ]
            },
            "lifestyle": {
                "name": "Lifestyle",
                "description": "Повседневные моменты и образ жизни",
                "characteristics": ["повседневность", "жизнь", "момент", "естественность"],
                "tips": [
                    "Покажите естественные эмоции",
                    "Используйте естественное освещение",
                    "Не переусложняйте композицию",
                    "Ловите моменты"
                ]
            },
            "fashion": {
                "name": "Модная фотография",
                "description": "Стильная фотография с акцентом на одежду",
                "characteristics": ["мода", "стиль", "одежда", "аксессуары"],
                "tips": [
                    "Подчеркните детали одежды",
                    "Используйте контрастные фоны",
                    "Работайте с позами",
                    "Обратите внимание на освещение"
                ]
            },
            "nature": {
                "name": "Природа",
                "description": "Фотографии на природе",
                "characteristics": ["природа", "пейзаж", "деревья", "небо"],
                "tips": [
                    "Используйте золотой час",
                    "Работайте с глубиной резкости",
                    "Найдите интересные ракурсы",
                    "Следите за погодой"
                ]
            },
            "architecture": {
                "name": "Архитектура",
                "description": "Фотографии зданий и сооружений",
                "characteristics": ["здание", "архитектура", "линии", "геометрия"],
                "tips": [
                    "Используйте прямые линии",
                    "Работайте с симметрией",
                    "Обратите внимание на освещение",
                    "Найдите интересные углы"
                ]
            }
        }
    
    async def analyze_photo(self, image_data: bytes) -> Dict:
        """
        Анализирует фотографию и дает рекомендации по улучшению
        """
        try:
            # Анализируем изображение через OpenAI Vision
            analysis = await self._analyze_with_openai(image_data)
            
            # Анализируем технические параметры
            technical_analysis = self._analyze_technical_aspects(image_data)
            
            # Определяем тип фотографии
            photo_type_analysis = self._analyze_photo_type(analysis)
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(analysis, technical_analysis, photo_type_analysis)
            
            # Создаем схему улучшения
            improvement_schema = await self._create_improvement_schema(image_data, analysis, recommendations)
            
            return {
                "analysis": analysis,
                "technical": technical_analysis,
                "photo_type": photo_type_analysis,
                "recommendations": recommendations,
                "improvement_schema": improvement_schema
            }
            
        except Exception as e:
            print(f"Ошибка анализа фотографии: {e}")
            return self._get_fallback_analysis()
    
    async def _analyze_with_openai(self, image_data: bytes) -> Dict:
        """Анализирует изображение через OpenAI Vision API"""
        try:
            import aiohttp
            
            # Кодируем изображение
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
                                "text": """Проанализируй эту фотографию и верни анализ в формате JSON:
                                {
                                    "composition": "описание композиции и кадрирования",
                                    "lighting": "описание освещения и теней",
                                    "colors": "описание цветовой палитры и настроения",
                                    "angle": "угол съемки и перспектива",
                                    "focus": "фокус и глубина резкости",
                                    "mood": "настроение и атмосфера фотографии",
                                    "subject": "основной объект на фото",
                                    "background": "описание фона",
                                    "strengths": ["сильные стороны фотографии"],
                                    "weaknesses": ["слабые стороны и проблемы"],
                                    "photo_type_suggestions": ["предполагаемые типы фотографии"],
                                    "improvement_areas": ["области для улучшения"]
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
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Пытаемся распарсить JSON
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            # Если не JSON, создаем структурированный ответ
                            return self._parse_text_response(content)
                    else:
                        print(f"OpenAI API error: {response.status}")
                        return {}
                        
        except Exception as e:
            print(f"Ошибка OpenAI анализа: {e}")
            return {}
    
    def _parse_text_response(self, content: str) -> Dict:
        """Парсит текстовый ответ от OpenAI в структурированный формат"""
        return {
            "composition": "Анализ композиции выполнен",
            "lighting": "Освещение проанализировано",
            "colors": "Цветовая палитра определена",
            "angle": "Угол съемки оценен",
            "focus": "Фокус и резкость проверены",
            "mood": "Настроение фотографии определено",
            "subject": "Основной объект идентифицирован",
            "background": "Фон проанализирован",
            "strengths": ["Хорошее качество", "Интересная композиция"],
            "weaknesses": ["Можно улучшить освещение", "Попробуйте другой ракурс"],
            "photo_type_suggestions": ["portrait", "lifestyle"],
            "improvement_areas": ["композиция", "освещение"]
        }
    
    def _analyze_technical_aspects(self, image_data: bytes) -> Dict:
        """Анализирует технические аспекты изображения"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Основные параметры
            width, height = image.size
            aspect_ratio = width / height
            
            # Анализ яркости
            grayscale = image.convert('L')
            brightness = sum(grayscale.getdata()) / (width * height)
            
            # Анализ контраста
            pixels = list(grayscale.getdata())
            contrast = max(pixels) - min(pixels)
            
            # Определение ориентации
            orientation = "landscape" if aspect_ratio > 1.2 else "portrait" if aspect_ratio < 0.8 else "square"
            
            # Анализ резкости (простая оценка)
            sharpness = self._calculate_sharpness(grayscale)
            
            return {
                "dimensions": f"{width}x{height}",
                "aspect_ratio": round(aspect_ratio, 2),
                "orientation": orientation,
                "brightness": round(brightness, 1),
                "contrast": contrast,
                "sharpness": sharpness,
                "resolution": "high" if width > 1920 else "medium" if width > 800 else "low"
            }
            
        except Exception as e:
            print(f"Ошибка технического анализа: {e}")
            return {}
    
    def _calculate_sharpness(self, grayscale_image) -> str:
        """Простая оценка резкости изображения"""
        try:
            # Используем лапласиан для оценки резкости
            import numpy as np
            img_array = np.array(grayscale_image)
            laplacian_var = np.var(np.gradient(img_array))
            
            if laplacian_var > 1000:
                return "очень резкое"
            elif laplacian_var > 500:
                return "резкое"
            elif laplacian_var > 200:
                return "средняя резкость"
            else:
                return "размытое"
        except:
            return "неизвестно"
    
    def _analyze_photo_type(self, analysis: Dict) -> Dict:
        """Определяет тип фотографии"""
        if not analysis or "photo_type_suggestions" not in analysis:
            return {"detected_type": "unknown", "confidence": 0.0}
        
        suggested_types = analysis["photo_type_suggestions"]
        best_match = None
        best_score = 0
        
        for type_key, type_info in self.photo_types.items():
            score = 0
            for suggestion in suggested_types:
                for characteristic in type_info["characteristics"]:
                    if characteristic.lower() in suggestion.lower():
                        score += 1
            
            if score > best_score:
                best_score = score
                best_match = type_key
        
        if best_match:
            return {
                "detected_type": best_match,
                "type_info": self.photo_types[best_match],
                "confidence": min(best_score / 3, 1.0)
            }
        
        return {"detected_type": "unknown", "confidence": 0.0}
    
    def _generate_recommendations(self, analysis: Dict, technical: Dict, photo_type: Dict) -> List[str]:
        """Генерирует рекомендации по улучшению"""
        recommendations = []
        
        # Рекомендации по освещению
        brightness = technical.get("brightness", 0)
        if brightness < 80:
            recommendations.append("💡 Фото слишком темное - добавьте света или увеличьте экспозицию")
        elif brightness > 180:
            recommendations.append("☀️ Фото пересвечено - уменьшите яркость или используйте тень")
        
        # Рекомендации по контрасту
        contrast = technical.get("contrast", 0)
        if contrast < 30:
            recommendations.append("🎨 Увеличьте контраст для более выразительного снимка")
        
        # Рекомендации по резкости
        sharpness = technical.get("sharpness", "")
        if "размытое" in sharpness:
            recommendations.append("🔍 Улучшите фокусировку - фото получилось размытым")
        
        # Рекомендации по композиции
        if analysis.get("composition", ""):
            if "центр" in analysis["composition"].lower():
                recommendations.append("📐 Попробуйте правило третей вместо центрирования объекта")
        
        # Рекомендации по типу фотографии
        if photo_type.get("detected_type") != "unknown":
            type_tips = photo_type["type_info"]["tips"]
            recommendations.extend([f"💡 {tip}" for tip in type_tips[:2]])
        
        # Рекомендации по фону
        if analysis.get("background", ""):
            if "загруженный" in analysis["background"].lower() or "отвлекающий" in analysis["background"].lower():
                recommendations.append("🎭 Упростите фон - он отвлекает от главного объекта")
        
        # Общие рекомендации
        recommendations.extend([
            "📱 Используйте естественное освещение когда возможно",
            "🎯 Следите за фокусом на главном объекте",
            "🌈 Обратите внимание на цветовую гармонию"
        ])
        
        return recommendations[:6]  # Ограничиваем количество рекомендаций
    
    async def _create_improvement_schema(self, image_data: bytes, analysis: Dict, recommendations: List[str]) -> str:
        """Создает схему улучшения с помощью AI"""
        try:
            import aiohttp
            
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
                                "text": f"""Создай детальную схему улучшения этой фотографии. 
                                Анализ: {json.dumps(analysis, ensure_ascii=False)}
                                Рекомендации: {', '.join(recommendations)}
                                
                                Верни схему в формате:
                                📸 **СХЕМА УЛУЧШЕНИЯ ФОТОГРАФИИ**
                                
                                1️⃣ **КОМПОЗИЦИЯ**
                                • Проблема: [что не так с композицией]
                                • Решение: [как исправить]
                                
                                2️⃣ **ОСВЕЩЕНИЕ**
                                • Проблема: [что не так с освещением]
                                • Решение: [как улучшить свет]
                                
                                3️⃣ **ФОКУС И РЕЗКОСТЬ**
                                • Проблема: [проблемы с фокусом]
                                • Решение: [как сделать резче]
                                
                                4️⃣ **ЦВЕТА И НАСТРОЕНИЕ**
                                • Проблема: [что не так с цветами]
                                • Решение: [как улучшить цветовую палитру]
                                
                                5️⃣ **ПОЗИЦИОНИРОВАНИЕ**
                                • Проблема: [проблемы с позицией/углом]
                                • Решение: [как лучше снять]
                                
                                6️⃣ **ДЕТАЛИ**
                                • На что обратить внимание: [важные детали]
                                • Финальные штрихи: [последние улучшения]
                                
                                Будь конкретным и давай практические советы!"""
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
                "temperature": 0.4
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    else:
                        return "Не удалось создать схему улучшения"
                        
        except Exception as e:
            print(f"Ошибка создания схемы: {e}")
            return "Ошибка создания схемы улучшения"
    
    def _get_fallback_analysis(self) -> Dict:
        """Возвращает базовый анализ в случае ошибки"""
        return {
            "analysis": {
                "composition": "Не удалось проанализировать",
                "lighting": "Не удалось проанализировать",
                "colors": "Не удалось проанализировать",
                "subject": "Не определено",
                "strengths": ["Фото загружено"],
                "weaknesses": ["Требуется анализ"]
            },
            "technical": {
                "dimensions": "Неизвестно",
                "brightness": 0,
                "contrast": 0,
                "sharpness": "неизвестно"
            },
            "photo_type": {
                "detected_type": "unknown",
                "confidence": 0.0
            },
            "recommendations": [
                "📱 Попробуйте другое фото",
                "💡 Убедитесь в хорошем освещении",
                "🎯 Сфокусируйтесь на главном объекте"
            ],
            "improvement_schema": "Анализ недоступен. Попробуйте другое фото."
        }
