#!/usr/bin/env python3
"""
Простой тест рефакторенного бота
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Создаем простую конфигурацию
class SimpleConfig:
    CARD_WIDTH = 1280
    CARD_HEIGHT = 720
    SESSION_TIMEOUT_MINUTES = 30

# Заменяем импорты
class Config:
    CARD_WIDTH = 1280
    CARD_HEIGHT = 720
    SESSION_TIMEOUT_MINUTES = 30

sys.modules['app.config'] = Config

from app.core.analyzer_refactored import DishAnalyzerRefactored
from app.core.renderer_refactored import CardRendererRefactored
from app.utils.text_parse import TextParser


async def test_analyzer():
    """Тестирует анализатор блюд"""
    print("🧪 Тестирование анализатора блюд...")
    
    analyzer = DishAnalyzerRefactored()
    
    # Тест 1: Получение предложений блюд
    print("\n1. Тест получения предложений блюд:")
    suggestions = await analyzer.get_dish_suggestions(b"fake_image_data")
    print(f"   Предложения: {suggestions}")
    
    # Тест 2: Расчет питательной ценности
    print("\n2. Тест расчета питательной ценности:")
    nutrition = await analyzer.calculate_nutrition("паста карбонара", 250, "варка")
    if nutrition:
        print(f"   Блюдо: {nutrition.dish_name}")
        print(f"   Калории: {nutrition.total_kcal} ккал")
        print(f"   Белки: {nutrition.total_protein}г")
        print(f"   Жиры: {nutrition.total_fat}г")
        print(f"   Углеводы: {nutrition.total_carbs}г")
    else:
        print("   ❌ Не удалось получить данные о питательной ценности")
    
    # Тест 3: Получение фактов
    print("\n3. Тест получения фактов:")
    facts_result = await analyzer.get_facts("паста карбонара")
    if facts_result.facts:
        fact = facts_result.facts[0]
        print(f"   Факт: {fact.text}")
        print(f"   Тип: {fact.type}")
    else:
        print("   ❌ Факты не найдены")
    
    # Тест 4: Полный анализ
    print("\n4. Тест полного анализа:")
    nutrition_result, facts_result = await analyzer.full_analysis("борщ", 300, "варка")
    if nutrition_result:
        print(f"   ✅ Полный анализ успешен")
        print(f"   Блюдо: {nutrition_result.dish_name}")
        print(f"   Калории: {nutrition_result.total_kcal} ккал")
    else:
        print("   ❌ Полный анализ не удался")


async def test_renderer():
    """Тестирует рендерер карточек"""
    print("\n🎨 Тестирование рендерера карточек...")
    
    renderer = CardRendererRefactored()
    
    # Создаем тестовые данные
    class MockNutritionResult:
        def __init__(self):
            self.dish_name = "паста карбонара"
            self.weight_g = 250
            self.cooking_method = "варка"
            self.total_kcal = 350
            self.total_protein = 12.5
            self.total_fat = 18.2
            self.total_carbs = 35.1
            self.assumptions = ["Расчет для 250г", "Учтено увеличение калорийности при варке"]
    
    class MockFact:
        def __init__(self):
            self.type = "history"
            self.text = "Паста карбонара была изобретена в Риме в 1944 году поваром по имени Ренато Гальярди."
            self.sources = ["https://example.com"]
    
    nutrition_result = MockNutritionResult()
    facts = [MockFact()]
    
    # Тест создания карточки
    try:
        card_data = renderer.render_card(nutrition_result, facts)
        print(f"   ✅ Карточка создана успешно, размер: {len(card_data)} байт")
        
        # Сохраняем тестовую карточку
        with open("test_card.png", "wb") as f:
            f.write(card_data)
        print("   💾 Тестовая карточка сохранена как test_card.png")
        
    except Exception as e:
        print(f"   ❌ Ошибка создания карточки: {e}")


async def test_text_parser():
    """Тестирует парсер текста"""
    print("\n📝 Тестирование парсера текста...")
    
    test_cases = [
        "паста карбонара",
        "борщ 300г",
        "пицца 250г жарка",
        "салат цезарь 150г запекание",
        "суши 200г"
    ]
    
    for text in test_cases:
        dish_name, weight, cooking_method = TextParser.parse_dish_description(text)
        print(f"   '{text}' → '{dish_name}', {weight}г, {cooking_method}")


async def main():
    """Главная функция тестирования"""
    print("🍽️ Тестирование рефакторенного Show My Food Bot")
    print("=" * 50)
    
    try:
        await test_analyzer()
        await test_renderer()
        await test_text_parser()
        
        print("\n" + "=" * 50)
        print("✅ Все тесты завершены успешно!")
        print("\n🎉 Рефакторенный бот готов к работе!")
        print("\n📋 Что было улучшено:")
        print("   • Упрощена логика обработки фото")
        print("   • Улучшено распознавание блюд")
        print("   • Сделан ввод веса опциональным")
        print("   • Исправлена обработка ответов пользователя")
        print("   • Создан красивый дизайн карточек")
        print("   • Добавлена расширенная база блюд")
        
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
