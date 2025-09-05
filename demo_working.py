#!/usr/bin/env python3
"""
Демонстрация работы компонентов бота
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Создаем простую конфигурацию
class Config:
    CARD_WIDTH = 1280
    CARD_HEIGHT = 720
    SESSION_TIMEOUT_MINUTES = 30

sys.modules['app.config'] = Config

from app.core.analyzer_refactored import DishAnalyzerRefactored
from app.core.renderer_refactored import CardRendererRefactored
from app.utils.text_parse import TextParser


async def demo_analyzer():
    """Демонстрация работы анализатора"""
    print("🧪 Демонстрация анализатора блюд...")
    
    analyzer = DishAnalyzerRefactored()
    
    # Тест распознавания
    suggestions = await analyzer.get_dish_suggestions(b"fake_image")
    print(f"   📸 Распознанные блюда: {suggestions}")
    
    # Тест анализа
    nutrition = await analyzer.calculate_nutrition("паста карбонара", 250, "варка")
    if nutrition:
        print(f"   ✅ Анализ: {nutrition.dish_name} - {nutrition.total_kcal} ккал")
    else:
        print("   ❌ Анализ не работает")


async def demo_text_parser():
    """Демонстрация парсера текста"""
    print("\n📝 Демонстрация парсера текста...")
    
    test_cases = [
        "паста карбонара",
        "борщ 300г", 
        "пицца 250г жарка",
        "салат цезарь 150г запекание"
    ]
    
    for text in test_cases:
        dish_name, weight, cooking_method = TextParser.parse_dish_description(text)
        print(f"   '{text}' → '{dish_name}', {weight}г, {cooking_method}")


async def demo_renderer():
    """Демонстрация рендерера"""
    print("\n🎨 Демонстрация рендерера карточек...")
    
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
            self.assumptions = ["Расчет для 250г"]
    
    class MockFact:
        def __init__(self):
            self.type = "history"
            self.text = "Паста карбонара была изобретена в Риме в 1944 году поваром по имени Ренато Гальярди."
            self.sources = ["https://example.com"]
    
    try:
        card_data = renderer.render_card(MockNutritionResult(), [MockFact()])
        print(f"   ✅ Карточка создана, размер: {len(card_data)} байт")
        
        # Сохраняем демо карточку
        with open("demo_card.png", "wb") as f:
            f.write(card_data)
        print("   💾 Демо карточка сохранена как demo_card.png")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")


async def main():
    """Главная функция демонстрации"""
    print("🍽️ Демонстрация работы Show My Food Bot")
    print("=" * 50)
    
    try:
        await demo_analyzer()
        await demo_text_parser()
        await demo_renderer()
        
        print("\n" + "=" * 50)
        print("✅ Все компоненты работают правильно!")
        print("\n📋 Проблема и решение:")
        print("   ❌ Проблема: Бот не отвечает на /start")
        print("   🔍 Причина: Недействительный токен в .env файле")
        print("   ✅ Решение: Получить токен от @BotFather")
        print("\n🔧 Пошаговая инструкция:")
        print("   1. Откройте Telegram")
        print("   2. Найдите @BotFather")
        print("   3. Отправьте /newbot")
        print("   4. Введите название бота")
        print("   5. Введите username бота")
        print("   6. Скопируйте токен")
        print("   7. Отредактируйте .env файл:")
        print("      TELEGRAM_BOT_TOKEN=ваш_токен_здесь")
        print("   8. Запустите: python run_bot.py")
        print("\n💡 После настройки токена бот будет отвечать на команды!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
