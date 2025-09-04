import os
import aiohttp
import json
from typing import List, Optional
from .fact_base import FactProvider, Fact, FactResult


class PerplexityFactProvider(FactProvider):
    """Провайдер фактов на основе Perplexity API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key не найден")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, query: str) -> Optional[dict]:
        """Выполняет запрос к Perplexity API"""
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты эксперт по кулинарии и истории блюд. Отвечай на русском языке. Предоставляй только проверенные факты с источниками. Всегда отвечай в формате JSON."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.2
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Perplexity API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Ошибка запроса к Perplexity: {e}")
            return None
    
    async def get_facts(
        self, 
        dish_name: str, 
        ingredients: List[str] = None,
        exclude_facts: List[str] = None
    ) -> FactResult:
        """
        Получает факты о блюде через Perplexity API
        """
        exclude_facts = exclude_facts or []
        
        # Формируем запрос по вашему промпту
        comma_separated_ingredients = ", ".join(ingredients) if ingredients else ""
        
        query = f'''Блюдо: "{dish_name}"
Ингредиенты: {comma_separated_ingredients}

Задача: дай 3–5 коротких факта (1–2 предложения каждый) о блюде и/или его ключевых ингредиентах.
Типы фактов: history, ingredient, event, celebrity.
Для каждого факта обязательно укажи:
- type (одно из: history|ingredient|event|celebrity)
- text (RU, 1–2 предложения, без кликбейта)
- sources (1–3 валидных URL, разные домены)
- confidence (0..1, честная оценка)
- verified (True/False). Для celebrity = True только при наличии проверяемых независимых источников.

Формат ответа: JSON-массив объектов с полями type, text, sources, verified, confidence.
Если данных недостаточно, верни пустой массив.'''
        
        response = await self._make_request(query)
        if not response:
            return FactResult(facts=[], total_found=0)
        
        # Парсим JSON ответ
        facts = self._parse_json_response(response, exclude_facts)
        
        # Фильтруем celebrity факты без верификации
        filtered_celebrity = 0
        verified_facts = []
        
        for fact in facts:
            if fact.type == "celebrity" and not fact.verified:
                filtered_celebrity += 1
                continue
            verified_facts.append(fact)
        
        return FactResult(
            facts=verified_facts,
            total_found=len(facts),
            filtered_celebrity=filtered_celebrity
        )
    
    def _parse_json_response(self, response: dict, exclude_facts: List[str]) -> List[Fact]:
        """Парсит JSON ответ от Perplexity и извлекает факты"""
        facts = []
        
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Очищаем контент от возможных markdown блоков
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            # Парсим JSON
            facts_data = json.loads(content.strip())
            
            if not isinstance(facts_data, list):
                print("Ответ не является массивом фактов")
                return facts
            
            for fact_data in facts_data:
                if not isinstance(fact_data, dict):
                    continue
                
                # Проверяем обязательные поля
                required_fields = ["type", "text", "sources", "verified", "confidence"]
                if not all(field in fact_data for field in required_fields):
                    continue
                
                # Валидируем тип факта
                fact_type = fact_data["type"]
                if fact_type not in ["history", "ingredient", "event", "celebrity"]:
                    continue
                
                # Валидируем текст
                text = fact_data["text"].strip()
                if not text or len(text) < 10:
                    continue
                
                # Исключаем уже показанные факты
                if text in exclude_facts:
                    continue
                
                # Валидируем источники
                sources = fact_data.get("sources", [])
                if not isinstance(sources, list) or len(sources) == 0:
                    continue
                
                # Валидируем верификацию
                verified = bool(fact_data.get("verified", False))
                
                # Валидируем confidence
                confidence = float(fact_data.get("confidence", 0.5))
                confidence = max(0.0, min(1.0, confidence))  # Ограничиваем 0-1
                
                facts.append(Fact(
                    type=fact_type,
                    text=text,
                    sources=sources,
                    verified=verified,
                    confidence=confidence
                ))
        
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON от Perplexity: {e}")
            print(f"Содержимое ответа: {content[:500]}...")
        except Exception as e:
            print(f"Ошибка обработки ответа Perplexity: {e}")
        
        return facts[:5]  # Максимум 5 фактов
    
    async def get_fallback_facts(self, exclude_facts: List[str] = None) -> List[Fact]:
        """
        Получает резервные факты через Perplexity
        """
        exclude_facts = exclude_facts or []
        
        query = '''Блюдо: "общие принципы кулинарии"
Ингредиенты: различные продукты

Задача: дай 2-3 коротких факта о кулинарии, здоровом питании или истории блюд в целом.
Типы фактов: history, ingredient, event.
Для каждого факта обязательно укажи:
- type (одно из: history|ingredient|event)
- text (RU, 1–2 предложения, без кликбейта)
- sources (1–3 валидных URL, разные домены)
- confidence (0..1, честная оценка)
- verified (True/False)

Формат ответа: JSON-массив объектов с полями type, text, sources, verified, confidence.'''
        
        response = await self._make_request(query)
        if not response:
            return []
        
        facts = self._parse_json_response(response, exclude_facts)
        return facts[:2]  # Максимум 2 резервных факта
    
    async def verify_celebrity_fact(self, fact_text: str) -> bool:
        """
        Верифицирует факт о селебрити через дополнительный запрос
        """
        query = f"Проверь и найди подтверждения этого факта: '{fact_text}'. Найди минимум 2 независимых источника."
        
        response = await self._make_request(query)
        if not response:
            return False
        
        try:
            content = response["choices"][0]["message"]["content"]
            # Считаем количество источников
            import re
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
            
            # Проверяем, что источники с разных доменов
            domains = set()
            for url in urls:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains.add(domain)
                except:
                    continue
            
            return len(domains) >= 2
        
        except Exception as e:
            print(f"Ошибка верификации: {e}")
            return False
