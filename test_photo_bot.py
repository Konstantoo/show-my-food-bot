#!/usr/bin/env python3
"""
Тест Photo Advice Bot
"""

import asyncio
import sys
import os
from io import BytesIO
from PIL import Image

# Добавляем путь к модулям
sys.path.append('.')

from app.config import Config
from app.core.photo_analyzer import PhotoAnalyzer, PhotoAnalysisResult
from app.core.advice_renderer import AdviceRenderer
from app.core.session import SessionStore


async def test_photo_analyzer():
    """Тестирует анализатор фотографий"""
    print("🔍 Тестирование анализатора фотографий...")
    
    analyzer = PhotoAnalyzer()
    
    # Создаем тестовое изображение
    test_image = Image.new('RGB', (1920, 1080), color='lightblue')
    image_data = BytesIO()
    test_image.save(image_data, format='JPEG')
    image_data.seek(0)
    
    # Тест анализа
    print("  📸 Тест анализа фото...")
    result = await analyzer.analyze_photo(image_data.getvalue())
    
    assert result is not None
    assert isinstance(result, PhotoAnalysisResult)
    assert 1 <= result.composition_score <= 10
    assert 1 <= result.lighting_score <= 10
    assert 1 <= result.technical_score <= 10
    assert 1 <= result.overall_score <= 10
    assert len(result.main_advice) > 0
    
    print(f"    ✅ Анализ завершен: {result.main_advice}")
    print(f"    ✅ Оценки: композиция={result.composition_score}, освещение={result.lighting_score}, техника={result.technical_score}")
    
    # Тест дополнительных советов
    print("  💡 Тест дополнительных советов...")
    additional_advice = await analyzer.get_additional_advice(result)
    assert isinstance(additional_advice, list)
    print(f"    ✅ Дополнительных советов: {len(additional_advice)}")
    
    print("✅ Анализатор фотографий работает корректно\n")


def test_advice_renderer():
    """Тестирует рендерер советов"""
    print("🎨 Тестирование рендерера советов...")
    
    renderer = AdviceRenderer()
    
    # Создаем тестовый результат анализа
    result = PhotoAnalysisResult(
        main_advice="Попробуйте использовать правило третей для лучшей композиции",
        composition_score=7,
        lighting_score=8,
        technical_score=6,
        overall_score=7,
        additional_advice=[
            "Обратите внимание на освещение",
            "Попробуйте другой угол съемки"
        ],
        mood="спокойное",
        style_suggestions=["минимализм", "черно-белое"]
    )
    
    # Тест создания карточки
    print("  🖼️ Тест создания карточки...")
    card_data = renderer.render_advice_card(result)
    assert card_data is not None
    assert len(card_data) > 0
    
    # Проверяем, что это валидное изображение
    try:
        img = Image.open(BytesIO(card_data))
        assert img.width == 1280
        assert img.height == 720
        print(f"    ✅ Карточка создана: {img.width}x{img.height}px")
    except Exception as e:
        print(f"    ❌ Ошибка создания карточки: {e}")
        return False
    
    print("✅ Рендерер советов работает корректно\n")
    return True


def test_session_store():
    """Тестирует хранилище сессий"""
    print("💾 Тестирование хранилища сессий...")
    
    store = SessionStore()
    
    # Тест создания сессии
    print("  👤 Тест создания сессии...")
    session = store.get_session(12345)
    assert session.user_id == 12345
    assert session.current_photo_analysis is None
    print("    ✅ Сессия создана")
    
    # Тест обновления состояния
    print("  🔄 Тест обновления состояния...")
    test_result = PhotoAnalysisResult(
        main_advice="Тестовый совет",
        composition_score=8,
        lighting_score=7,
        technical_score=9,
        overall_score=8
    )
    
    session.current_photo_analysis = test_result
    session.add_advice_shown("тестовый совет")
    
    assert session.current_photo_analysis == test_result
    assert "тестовый совет" in session.advice_shown
    print("    ✅ Состояние обновлено")
    
    # Тест сброса состояния
    print("  🔄 Тест сброса состояния...")
    session.reset_photo_state()
    assert session.current_photo_analysis is None
    print("    ✅ Состояние сброшено")
    
    print("✅ Хранилище сессий работает корректно\n")


async def test_integration():
    """Интеграционный тест"""
    print("🔗 Интеграционный тест...")
    
    # Создаем все компоненты
    analyzer = PhotoAnalyzer()
    renderer = AdviceRenderer()
    store = SessionStore()
    
    # Симулируем полный цикл работы
    print("  📱 Симуляция работы бота...")
    
    # 1. Создаем тестовое изображение
    test_image = Image.new('RGB', (1280, 720), color='lightgreen')
    image_data = BytesIO()
    test_image.save(image_data, format='JPEG')
    image_data.seek(0)
    
    # 2. Получаем сессию пользователя
    session = store.get_session(12345)
    
    # 3. Выполняем анализ
    analysis_result = await analyzer.analyze_photo(image_data.getvalue())
    
    # 4. Сохраняем результат в сессию
    session.current_photo_analysis = analysis_result
    session.add_advice_shown(analysis_result.main_advice)
    
    # 5. Создаем карточку
    card_data = renderer.render_advice_card(analysis_result)
    
    # Проверяем результат
    assert analysis_result is not None
    assert card_data is not None
    assert len(card_data) > 0
    
    print(f"    ✅ Анализ: {analysis_result.main_advice}")
    print(f"    ✅ Оценка: {analysis_result.overall_score}/10")
    print(f"    ✅ Размер карточки: {len(card_data)} байт")
    
    print("✅ Интеграционный тест пройден\n")


async def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестирования Photo Advice Bot\n")
    
    try:
        # Проверяем конфигурацию
        print("⚙️ Проверка конфигурации...")
        Config.validate()
        print("✅ Конфигурация валидна\n")
        
        # Запускаем тесты
        await test_photo_analyzer()
        test_advice_renderer()
        test_session_store()
        await test_integration()
        
        print("🎉 Все тесты пройдены успешно!")
        print("✅ Photo Advice Bot готов к работе!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
