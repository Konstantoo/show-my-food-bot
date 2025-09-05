import json
import random
import aiohttp
from typing import List, Optional, Dict
from dataclasses import dataclass

from app.config import Config


@dataclass
class Quote:
    """Цитата мастера фотографии/кинематографа"""
    text: str
    author: str
    profession: str  # фотограф, режиссер, художник, оператор
    context: str = ""  # контекст применения
    relevance_score: float = 1.0


class QuotesProvider:
    """Провайдер цитат известных мастеров фотографии и кинематографа"""
    
    def __init__(self):
        self.perplexity_api_key = Config.PERPLEXITY_API_KEY
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        
        # База локальных цитат для fallback
        self.local_quotes = {
            "composition": [
                Quote(
                    text="Композиция — это самое важное в фотографии. Все остальное можно исправить в пост-обработке.",
                    author="Анри Картье-Брессон",
                    profession="фотограф",
                    context="правило третей, баланс"
                ),
                Quote(
                    text="Фотография — это не то, что вы видите, а то, что вы чувствуете.",
                    author="Дон Маккаллин",
                    profession="фотограф",
                    context="эмоциональная композиция"
                ),
                Quote(
                    text="В каждом кадре должна быть история.",
                    author="Стэнли Кубрик",
                    profession="режиссер",
                    context="повествовательная композиция"
                ),
                Quote(
                    text="Симметрия — это смерть искусства.",
                    author="Василий Кандинский",
                    profession="художник",
                    context="асимметричная композиция"
                )
            ],
            "lighting": [
                Quote(
                    text="Свет делает фотографию. Объемлите свет. Восхищайтесь им. Любите его. Но прежде всего, знайте свет.",
                    author="Джордж Истман",
                    profession="фотограф",
                    context="работа со светом"
                ),
                Quote(
                    text="Фотография — это живопись светом.",
                    author="Марк Рибу",
                    profession="фотограф",
                    context="естественное освещение"
                ),
                Quote(
                    text="Тень так же важна, как и свет.",
                    author="Грегг Толанд",
                    profession="оператор",
                    context="контрастное освещение"
                ),
                Quote(
                    text="Золотой час — это магия, которую нельзя воссоздать искусственно.",
                    author="Марк Адамус",
                    profession="фотограф",
                    context="естественный свет"
                )
            ],
            "technical": [
                Quote(
                    text="Лучшая камера — та, которая у вас с собой.",
                    author="Чейз Джарвис",
                    profession="фотограф",
                    context="техническое качество"
                ),
                Quote(
                    text="Резкость — это буржуазная концепция.",
                    author="Анри Картье-Брессон",
                    profession="фотограф",
                    context="техническое совершенство"
                ),
                Quote(
                    text="Каждый объектив видит мир по-своему.",
                    author="Роджер Дикинс",
                    profession="оператор",
                    context="выбор объектива"
                )
            ],
            "mood": [
                Quote(
                    text="Фотография — это способ чувствовать, касаться, любить. То, что вы поймали на пленку, захвачено навсегда.",
                    author="Аарон Сискинд",
                    profession="фотограф",
                    context="эмоциональное воздействие"
                ),
                Quote(
                    text="Цвет — это место, где встречаются наш мозг и Вселенная.",
                    author="Пол Сезанн",
                    profession="художник",
                    context="цветовое настроение"
                ),
                Quote(
                    text="В кинематографе важно не то, что показано, а то, что скрыто.",
                    author="Роберт Брессон",
                    profession="режиссер",
                    context="атмосфера и настроение"
                )
            ],
            "style": [
                Quote(
                    text="Стиль — это способ сказать, кто вы, не произнося ни слова.",
                    author="Рэйчел Зои",
                    profession="стилист",
                    context="личный стиль"
                ),
                Quote(
                    text="Минимализм — это не недостаток чего-то. Это точно правильное количество чего-то.",
                    author="Николас Бурро",
                    profession="дизайнер",
                    context="минималистичный стиль"
                ),
                Quote(
                    text="Каждая фотография — это автопортрет.",
                    author="Ансель Адамс",
                    profession="фотограф",
                    context="авторский стиль"
                )
            ]
        }
    
    async def get_relevant_quote(self, photo_analysis, context: str = "") -> Optional[Quote]:
        """Получает релевантную цитату на основе анализа фото"""
        try:
            # Сначала пробуем Perplexity API
            if self.perplexity_api_key and self.perplexity_api_key != "your_perplexity_api_key_here":
                perplexity_quote = await self._get_quote_from_perplexity(photo_analysis, context)
                if perplexity_quote:
                    return perplexity_quote
            
            # Fallback на локальные цитаты
            return self._get_local_quote(photo_analysis, context)
            
        except Exception as e:
            print(f"Ошибка получения цитаты: {e}")
            return self._get_local_quote(photo_analysis, context)
    
    async def _get_quote_from_perplexity(self, photo_analysis, context: str) -> Optional[Quote]:
        """Получает цитату через Perplexity API"""
        try:
            # Формируем описание фото для поиска цитаты
            photo_description = self._create_photo_description(photo_analysis)
            
            prompt = f"""
            Найди подходящую цитату известного фотографа, художника, режиссера или оператора, которая подходит к этой фотографии:
            
            Описание фото: {photo_description}
            Контекст: {context}
            
            Верни ответ в формате JSON:
            {{
                "text": "текст цитаты на русском языке",
                "author": "имя автора",
                "profession": "профессия (фотограф/художник/режиссер/оператор)",
                "context": "почему эта цитата подходит к фото",
                "relevance_score": 0.9
            }}
            
            Ищи цитаты, которые говорят о композиции, свете, настроении, технике или философии фотографии.
            Предпочитай известных мастеров: Анри Картье-Брессон, Ансель Адамс, Роберт Капа, Стэнли Кубрик, 
            Роджер Дикинс, Эммануэль Любецки, Леонардо да Винчи, Пикассо и др.
            """
            
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты эксперт по истории фотографии, кинематографа и изобразительного искусства. Ты знаешь множество цитат известных мастеров."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.perplexity_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Парсим JSON ответ
                        try:
                            quote_data = json.loads(content)
                            return Quote(
                                text=quote_data.get('text', ''),
                                author=quote_data.get('author', 'Неизвестный мастер'),
                                profession=quote_data.get('profession', 'мастер'),
                                context=quote_data.get('context', ''),
                                relevance_score=quote_data.get('relevance_score', 0.8)
                            )
                        except json.JSONDecodeError:
                            # Если не JSON, пробуем извлечь цитату из текста
                            return self._parse_text_response(content)
                    else:
                        print(f"Perplexity API error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Ошибка Perplexity API: {e}")
            return None
    
    def _create_photo_description(self, photo_analysis) -> str:
        """Создает описание фото для поиска цитаты"""
        description_parts = []
        
        # Основной совет
        description_parts.append(f"Главная особенность: {photo_analysis.main_advice}")
        
        # Оценки
        if photo_analysis.composition_score >= 8:
            description_parts.append("отличная композиция")
        elif photo_analysis.composition_score <= 5:
            description_parts.append("композиция требует улучшения")
        
        if photo_analysis.lighting_score >= 8:
            description_parts.append("хорошее освещение")
        elif photo_analysis.lighting_score <= 5:
            description_parts.append("освещение можно улучшить")
        
        # Настроение
        description_parts.append(f"настроение: {photo_analysis.mood}")
        
        # Стиль
        if photo_analysis.style_suggestions:
            description_parts.append(f"стиль: {', '.join(photo_analysis.style_suggestions[:2])}")
        
        return "; ".join(description_parts)
    
    def _parse_text_response(self, content: str) -> Optional[Quote]:
        """Парсит текстовый ответ от Perplexity"""
        try:
            # Простой парсинг цитаты из текста
            lines = content.strip().split('\n')
            quote_text = ""
            author = "Неизвестный мастер"
            
            for line in lines:
                if '"' in line and not author.startswith("Неизвестный"):
                    quote_text = line.strip().strip('"')
                elif any(word in line.lower() for word in ['автор', 'сказал', '—', '-']):
                    author = line.split('—')[-1].split('-')[-1].strip()
            
            if quote_text:
                return Quote(
                    text=quote_text,
                    author=author,
                    profession="мастер",
                    context="подобрано по смыслу фотографии"
                )
        except:
            pass
        
        return None
    
    def _get_local_quote(self, photo_analysis, context: str) -> Quote:
        """Получает локальную цитату на основе анализа"""
        # Определяем категорию на основе анализа
        category = "composition"  # по умолчанию
        
        if photo_analysis.lighting_score <= 6:
            category = "lighting"
        elif photo_analysis.technical_score <= 6:
            category = "technical"
        elif "настроение" in context.lower() or "атмосфера" in context.lower():
            category = "mood"
        elif "стиль" in context.lower():
            category = "style"
        
        # Выбираем случайную цитату из категории
        quotes = self.local_quotes.get(category, self.local_quotes["composition"])
        selected_quote = random.choice(quotes)
        
        # Устанавливаем релевантность
        selected_quote.relevance_score = self._calculate_relevance(selected_quote, photo_analysis)
        
        return selected_quote
    
    def _calculate_relevance(self, quote: Quote, photo_analysis) -> float:
        """Рассчитывает релевантность цитаты к фото"""
        relevance = 0.7  # базовая релевантность
        
        # Увеличиваем релевантность на основе совпадений
        if "композиция" in quote.context and photo_analysis.composition_score >= 7:
            relevance += 0.2
        elif "свет" in quote.context and photo_analysis.lighting_score >= 7:
            relevance += 0.2
        elif "техник" in quote.context and photo_analysis.technical_score >= 7:
            relevance += 0.2
        
        return min(1.0, relevance)
    
    async def get_multiple_quotes(self, photo_analysis, count: int = 3) -> List[Quote]:
        """Получает несколько релевантных цитат"""
        quotes = []
        
        contexts = ["композиция", "освещение", "техника", "настроение", "стиль"]
        
        for context in contexts[:count]:
            quote = await self.get_relevant_quote(photo_analysis, context)
            if quote and quote not in quotes:
                quotes.append(quote)
        
        # Дополняем локальными цитатами если нужно
        while len(quotes) < count:
            local_quote = self._get_local_quote(photo_analysis, random.choice(contexts))
            if local_quote not in quotes:
                quotes.append(local_quote)
        
        # Сортируем по релевантности
        quotes.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return quotes[:count]
