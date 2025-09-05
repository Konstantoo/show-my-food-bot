#!/usr/bin/env python3
"""
Запуск Photo Analyzer Bot - бота для анализа и улучшения фотографий
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.bot.photo_analyzer_bot import main

if __name__ == "__main__":
    try:
        print("📸 Запуск Photo Analyzer Bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
