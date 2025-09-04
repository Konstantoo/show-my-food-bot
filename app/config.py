import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    BOT_MODE = os.getenv("BOT_MODE", "polling")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    
    # Настройки приложения
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
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
        required_vars = [
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        
        return True


