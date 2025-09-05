#!/usr/bin/env python3
"""
Настройка для PythonAnywhere
Запустите этот файл как Always-On Task
"""

import os
import sys
import logging

# Добавляем путь к проекту
project_path = '/home/yourusername/photo-advice-bot'
sys.path.insert(0, project_path)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/yourusername/bot.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    try:
        from app.bot.photo_advice_bot import main
        import asyncio
        
        print("🚀 Запуск Photo Advice Bot на PythonAnywhere...")
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")
        raise
