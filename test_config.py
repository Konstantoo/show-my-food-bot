#!/usr/bin/env python3
"""
Тестовая конфигурация для проверки работы бота
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class TestConfig:
    """Тестовая конфигурация приложения"""
    
    # Telegram Bot (тестовый токен)
    TELEGRAM_BOT_TOKEN = "1234567890:TEST_TOKEN_FOR_DEVELOPMENT"
    BOT_MODE = "polling"
    
    # API Keys (заглушки)
    OPENAI_API_KEY = "test_openai_key"
    PERPLEXITY_API_KEY = "test_perplexity_key"
    
    # Настройки приложения
    DEBUG = True
    LOG_LEVEL = "INFO"
    
    # Настройки сессий
    SESSION_TIMEOUT_MINUTES = 30
    
    # Настройки карточек
    CARD_WIDTH = 1280
    CARD_HEIGHT = 720
    
    # Настройки фактов
    MAX_FACTS_PER_DISH = 3
    MAX_FALLBACK_FACTS = 2
    
    @classmethod
    def validate(cls):
        """Проверяет обязательные настройки"""
        return True
