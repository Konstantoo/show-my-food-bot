#!/usr/bin/env python3
"""
Запуск Photo Advice Bot
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append('.')

from app.bot.photo_advice_bot import main

if __name__ == "__main__":
    print("🚀 Запуск Photo Advice Bot...")
    asyncio.run(main())
