#!/usr/bin/env python3
"""
Тестовый скрипт для проверки компонентов бота
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.analyzer import DishAnalyzer
from app.core.renderer import CardRenderer
from app.core.providers.nutrition_table import TableNutritionProvider
from app.core.providers.hybrid_fact import HybridFactProvider
from app.utils.text_parse import TextParser


async def test_nutrition_provider():
    """Тестирует провайдер питательной ценности"""
    print("🧪 Тестирование Nutrition Provider...")
    
    provider = TableNutritionProvider()
    
    # Тест получения информации о блюде
    nutrition_info = await provider.get_nutrition_info("паста карбонара")
    if nutrition_info:
        print(f"✅ Найдена информация о пасте карбонара: {nutrition_info.kcal_per_100g} ккал/100г")
    else:
        print("❌ Информация о пасте карбонара не найдена")
    
    # Тест расчета питательной ценности
    result = await provider.calculate_nutrition("паста карбонара", 250, "запекание")
    if result:
        print(f"✅ Расчет для 250г запеченной пасты: {result.total_kcal} ккал")
        print(f"   Белки: {result.total_protein}г, Жиры: {result.total_fat}г, Углеводы: {result.total_carbs}г")
    else:
        print("❌ Ошибка расчета питательной ценности")


async def test_fact_provider():
    """Тестирует провайдер фактов"""
    print("\n🧪 Тестирование Fact Provider...")
    
    provider = HybridFactProvider(use_perplexity=False)  # Только локальные факты для теста
    
    # Тест получения фактов
    result = await provider.get_facts("паста карбонара", ["паста", "бекон", "яйцо"])
    if result.facts:
        print(f"✅ Найдено {len(result.facts)} фактов о пасте карбонара")
        for fact in result.facts:
            print(f"   - {fact.type}: {fact.text[:50]}...")
    else:
        print("❌ Факты о пасте карбонара не найдены")
    
    # Тест резервных фактов
    fallback_facts = await provider.get_fallback_facts()
    if fallback_facts:
        print(f"✅ Найдено {len(fallback_facts)} резервных фактов")
    else:
        print("❌ Резервные факты не найдены")


def test_text_parser():
    """Тестирует парсер текста"""
    print("\n🧪 Тестирование Text Parser...")
    
    test_cases = [
        "паста карбонара 250г запеченная",
        "борщ 300г",
        "плов",
        "салат цезарь 200г"
    ]
    
    for text in test_cases:
        dish_name, weight, cooking_method = TextParser.parse_dish_description(text)
        print(f"✅ '{text}' -> '{dish_name}' ({weight}г, {cooking_method})")


async def test_analyzer():
    """Тестирует анализатор блюд"""
    print("\n🧪 Тестирование Dish Analyzer...")
    
    analyzer = DishAnalyzer()
    
    # Тест полного анализа
    nutrition_result, facts_result = await analyzer.full_analysis(
        "паста карбонара", 250, "запекание"
    )
    
    if nutrition_result:
        print(f"✅ Анализ пасты карбонара: {nutrition_result.total_kcal} ккал")
    else:
        print("❌ Ошибка анализа питательной ценности")
    
    if facts_result.facts:
        print(f"✅ Найдено {len(facts_result.facts)} фактов")
    else:
        print("❌ Факты не найдены")


def test_renderer():
    """Тестирует рендерер карточек"""
    print("\n🧪 Тестирование Card Renderer...")
    
    try:
        renderer = CardRenderer()
        print("✅ Рендерер инициализирован успешно")
        
        # Создаем тестовые данные
        from app.core.providers.nutrition_base import NutritionResult, NutritionInfo
        
        nutrition_info = NutritionInfo(
            kcal_per_100g=350,
            protein=12,
            fat=18,
            carbs=35,
            notes="Тестовое блюдо"
        )
        
        nutrition_result = NutritionResult(
            dish_name="паста карбонара",
            weight_g=250,
            cooking_method="запекание",
            nutrition=nutrition_info,
            total_kcal=437.5,
            total_protein=30.0,
            total_fat=45.0,
            total_carbs=87.5,
            confidence=0.8,
            assumptions=["Учтено увеличение калорийности при запекании"]
        )
        
        # Тест рендеринга
        card_data = renderer.render_card(nutrition_result)
        print(f"✅ Карточка сгенерирована: {len(card_data)} байт")
        
    except Exception as e:
        print(f"❌ Ошибка рендерера: {e}")


async def main():
    """Главная функция тестирования"""
    print("🍽️ Тестирование Show My Food Bot\n")
    
    try:
        # Тестируем компоненты
        test_text_parser()
        await test_nutrition_provider()
        await test_fact_provider()
        await test_analyzer()
        test_renderer()
        
        print("\n🎉 Все тесты завершены!")
        
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
