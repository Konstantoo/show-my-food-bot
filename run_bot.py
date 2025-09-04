#!/usr/bin/env python3
"""
Запуск Telegram бота Show My Food
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.bot.main import main

if __name__ == "__main__":
    try:
        print("🍽️ Запуск Show My Food Bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
