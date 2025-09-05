import asyncio
import logging
from io import BytesIO
from typing import Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import Config
from app.core.universal_photo_analyzer import UniversalPhotoAnalyzer
from app.core.modern_photo_renderer import ModernPhotoRenderer
from app.core.session import SessionStore
from app.utils.file_utils import FileUtils

# Настройка логирования
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


class PhotoAnalyzerBot:
    """Telegram бот для анализа и улучшения фотографий"""
    
    def __init__(self):
        # Инициализация компонентов
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.session_store = SessionStore()
        
        # Инициализируем анализатор и рендерер
        if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != "your_openai_api_key_here":
            self.analyzer = UniversalPhotoAnalyzer(Config.OPENAI_API_KEY)
        else:
            self.analyzer = None
        
        self.renderer = ModernPhotoRenderer()
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_analyze, Command("analyze"))
        
        # Обработка фото
        self.dp.message.register(self.handle_photo, F.photo)
        
        # Обработка текста
        self.dp.message.register(self.handle_text, F.text)
        
        # Обработка callback запросов
        self.dp.callback_query.register(self.handle_callback)
    
    async def cmd_start(self, message: types.Message):
        """Обработчик команды /start"""
        welcome_text = """
📸 **Добро пожаловать в Photo Analyzer!**

Я помогу вам улучшить ваши фотографии с помощью ИИ-анализа.

**🎯 Что я умею:**
• Анализировать композицию и освещение
• Определять тип фотографии (портрет, пейзаж, мода)
• Давать конкретные рекомендации по улучшению
• Создавать визуальные схемы улучшения

**📱 Как пользоваться:**
• Отправьте фото для анализа
• Получите детальный анализ и рекомендации
• Используйте советы для улучшения снимков

**🔍 Команды:**
/help - подробная помощь
/analyze - начать анализ

**💡 Поддерживаемые типы:**
• Портреты и селфи
• Фотографии в полный рост
• Модные снимки
• Пейзажи и природа
• Архитектура
• Lifestyle фотографии

**Отправьте фото и начните улучшать свои снимки! ✨**
        """
        
        await message.answer(welcome_text)
    
    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help"""
        help_text = """
🆘 **Помощь по использованию Photo Analyzer**

**📸 Анализ фотографий:**
• Отправьте любое фото
• Получите детальный анализ композиции, освещения, цветов
• Узнайте тип вашей фотографии
• Получите конкретные рекомендации по улучшению

**🎯 Что анализируется:**
• **Композиция** - расположение объектов, правило третей
• **Освещение** - яркость, тени, контраст
• **Цвета** - палитра, настроение, гармония
• **Фокус** - резкость, глубина резкости
• **Угол съемки** - перспектива, ракурс
• **Фон** - отвлекающие элементы, простота

**💡 Типы фотографий:**
• **Портрет** - лицо крупным планом
• **В полный рост** - человек целиком
• **Lifestyle** - повседневные моменты
• **Мода** - стильные снимки
• **Природа** - пейзажи, растения
• **Архитектура** - здания, сооружения

**🔧 Рекомендации включают:**
• Конкретные советы по улучшению
• Технические параметры
• Композиционные правила
• Советы по освещению
• Работа с цветом и настроением

**📱 Просто отправьте фото и получите профессиональный анализ!**
        """
        
        await message.answer(help_text)
    
    async def cmd_analyze(self, message: types.Message):
        """Обработчик команды /analyze"""
        await message.answer("📸 Отправьте фотографию для анализа!\n\nЯ проанализирую композицию, освещение, цвета и дам рекомендации по улучшению.")
    
    async def handle_photo(self, message: types.Message):
        """Обработчик фото"""
        try:
            # Проверяем наличие анализатора
            if not self.analyzer:
                await message.answer("❌ OpenAI API не настроен. Обратитесь к администратору.")
                return
            
            # Получаем фото с наилучшим качеством
            photo = message.photo[-1]
            
            # Скачиваем фото
            file_info = await self.bot.get_file(photo.file_id)
            file_url = f"https://api.telegram.org/file/bot{Config.TELEGRAM_BOT_TOKEN}/{file_info.file_path}"
            
            # Скачиваем данные фото
            image_data = await FileUtils.download_image(file_url)
            if not image_data:
                await message.answer("❌ Ошибка загрузки фото. Попробуйте еще раз.")
                return
            
            # Проверяем размер фото
            if FileUtils.is_image_too_large(image_data):
                await message.answer("❌ Фото слишком большое. Максимальный размер: 20 МБ.")
                return
            
            # Сжимаем изображение для OpenAI (максимум 1024x1024 для экономии токенов)
            image_data = FileUtils.resize_image_if_needed(image_data, max_width=1024, max_height=1024, quality=80)
            
            # Анализируем фото
            await message.answer("🔍 Анализирую фотографию...")
            
            analysis_data = await self.analyzer.analyze_photo(image_data)
            
            # Создаем карточку с анализом
            card_data = self.renderer.render_photo_analysis_card(analysis_data)
            
            # Формируем текстовый ответ
            text_response = self._format_analysis_text(analysis_data)
            
            # Отправляем результат
            photo_file = InputFile(BytesIO(card_data), filename="photo_analysis.png")
            await message.answer_photo(
                photo=photo_file,
                caption=text_response
            )
            
            # Создаем клавиатуру с дополнительными действиями
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text="📋 Детальная схема",
                callback_data="detailed_schema"
            ))
            keyboard.add(InlineKeyboardButton(
                text="🔄 Новый анализ",
                callback_data="new_analysis"
            ))
            keyboard.add(InlineKeyboardButton(
                text="💡 Советы по типу фото",
                callback_data="photo_tips"
            ))
            
            keyboard.adjust(1)
            
            await message.answer(
                "✨ Анализ завершен! Что хотите сделать дальше?",
                reply_markup=keyboard.as_markup()
            )
            
            # Сохраняем в сессию
            session = self.session_store.get_session(message.from_user.id)
            session.photo_analysis = analysis_data
        
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await message.answer("❌ Ошибка анализа фото. Попробуйте еще раз.")
    
    async def handle_text(self, message: types.Message):
        """Обработчик текстовых сообщений"""
        text = message.text.strip()
        
        if text.lower() in ['анализ', 'analyze', 'фото', 'photo']:
            await self.cmd_analyze(message)
        else:
            await message.answer("📸 Отправьте фотографию для анализа или используйте команду /help")
    
    def _format_analysis_text(self, analysis_data: Dict) -> str:
        """Форматирует текстовый ответ с анализом"""
        analysis = analysis_data.get('analysis', {})
        technical = analysis_data.get('technical', {})
        photo_type = analysis_data.get('photo_type', {})
        
        text = "📸 **АНАЛИЗ ФОТОГРАФИИ**\n\n"
        
        # Основной объект
        if analysis.get('subject'):
            text += f"🎯 **Объект:** {analysis['subject']}\n"
        
        # Тип фотографии
        if photo_type.get('detected_type') != 'unknown':
            type_info = photo_type.get('type_info', {})
            text += f"🎭 **Тип:** {type_info.get('name', 'Неизвестный')}\n"
        
        # Технические параметры
        text += f"📱 **Разрешение:** {technical.get('resolution', 'Неизвестно')}\n"
        text += f"💡 **Яркость:** {technical.get('brightness', 0)}\n"
        text += f"🔍 **Резкость:** {technical.get('sharpness', 'Неизвестно')}\n\n"
        
        # Сильные стороны
        strengths = analysis.get('strengths', [])
        if strengths:
            text += "✅ **Сильные стороны:**\n"
            for strength in strengths[:3]:
                text += f"• {strength}\n"
            text += "\n"
        
        # Области для улучшения
        weaknesses = analysis.get('weaknesses', [])
        if weaknesses:
            text += "⚠️ **Области для улучшения:**\n"
            for weakness in weaknesses[:3]:
                text += f"• {weakness}\n"
        
        return text
    
    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик callback запросов"""
        await callback.answer()
        
        data = callback.data
        session = self.session_store.get_session(callback.from_user.id)
        
        if data == "detailed_schema":
            # Детальная схема улучшения
            if hasattr(session, 'photo_analysis') and session.photo_analysis:
                schema = session.photo_analysis.get('improvement_schema', 'Схема недоступна')
                await callback.message.answer(f"📋 **ДЕТАЛЬНАЯ СХЕМА УЛУЧШЕНИЯ**\n\n{schema}")
            else:
                await callback.message.answer("❌ Сначала проанализируйте фотографию.")
        
        elif data == "new_analysis":
            # Новый анализ
            await callback.message.answer("📸 Отправьте новую фотографию для анализа!")
        
        elif data == "photo_tips":
            # Советы по типу фото
            if hasattr(session, 'photo_analysis') and session.photo_analysis:
                photo_type = session.photo_analysis.get('photo_type', {})
                if photo_type.get('detected_type') != 'unknown':
                    type_info = photo_type.get('type_info', {})
                    tips = type_info.get('tips', [])
                    
                    tips_text = f"💡 **Советы для {type_info.get('name', 'фотографии')}:**\n\n"
                    for tip in tips:
                        tips_text += f"• {tip}\n"
                    
                    await callback.message.answer(tips_text)
                else:
                    await callback.message.answer("❌ Тип фотографии не определен. Попробуйте другой снимок.")
            else:
                await callback.message.answer("❌ Сначала проанализируйте фотографию.")
    
    async def start_polling(self):
        """Запускает бота в режиме polling"""
        try:
            # Очистка истекших сессий каждые 5 минут
            asyncio.create_task(self._cleanup_sessions_periodically())
            
            logger.info("Запуск Photo Analyzer Bot в режиме polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
    
    async def _cleanup_sessions_periodically(self):
        """Периодическая очистка истекших сессий"""
        while True:
            await asyncio.sleep(300)  # 5 минут
            self.session_store.cleanup_expired_sessions()


async def main():
    """Главная функция"""
    try:
        # Проверяем конфигурацию
        Config.validate()
        
        # Создаем и запускаем бота
        bot = PhotoAnalyzerBot()
        await bot.start_polling()
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
