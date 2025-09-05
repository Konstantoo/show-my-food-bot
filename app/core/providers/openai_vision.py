import base64
import json
from typing import List
from .vision_base import VisionLabelProvider, VisionResult


class OpenAIVisionProvider(VisionLabelProvider):
    """Провайдер анализа изображений через OpenAI Vision API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def analyze_image(self, image_data: bytes) -> List[VisionResult]:
        """
        Анализирует изображение через OpenAI Vision API
        """
        try:
            import aiohttp
            
            # Кодируем изображение в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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
                                "text": """Проанализируй это изображение еды и определи, что это за блюдо. 
                                Верни ответ в формате JSON с массивом блюд, каждое с полями:
                                - name: название блюда на русском языке
                                - confidence: уверенность от 0.0 до 1.0
                                - description: краткое описание
                                
                                Верни до 3 наиболее вероятных вариантов блюд.
                                Пример ответа:
                                [
                                    {"name": "паста карбонара", "confidence": 0.9, "description": "Итальянская паста с беконом и сыром"},
                                    {"name": "спагетти болоньезе", "confidence": 0.7, "description": "Паста с мясным соусом"}
                                ]"""
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
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Парсим JSON ответ
                        try:
                            dishes_data = json.loads(content)
                            results = []
                            
                            for dish in dishes_data:
                                results.append(VisionResult(
                                    label=dish['name'],
                                    confidence=dish['confidence'],
                                    description=dish['description']
                                ))
                            
                            return results
                            
                        except json.JSONDecodeError:
                            # Если не удалось распарсить JSON, возвращаем общий результат
                            return [VisionResult(
                                label="неизвестное блюдо",
                                confidence=0.5,
                                description="Не удалось определить блюдо"
                            )]
                    else:
                        print(f"OpenAI API error: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Ошибка анализа изображения через OpenAI: {e}")
            return []
    
    async def get_dish_suggestions(self, image_data: bytes) -> List[str]:
        """
        Возвращает предложения блюд на основе анализа изображения
        """
        results = await self.analyze_image(image_data)
        return [result.label for result in results]
