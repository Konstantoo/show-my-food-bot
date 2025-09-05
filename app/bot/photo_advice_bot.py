import asyncio
import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import Config
from app.core.photo_analyzer import PhotoAnalyzer
from app.core.advice_renderer import AdviceRenderer
from app.core.session import SessionStore
from app.utils.file_utils import FileUtils

# Настройка логирования
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


class PhotoAdviceBot:
    """Telegram бот для анализа фотографий и предоставления советов"""
    
    def __init__(self):
        # Инициализация компонентов
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.session_store = SessionStore()
        self.analyzer = PhotoAnalyzer()
        self.renderer = AdviceRenderer()
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_reset, Command("reset"))
        
        # Обработка фото
        self.dp.message.register(self.handle_photo, F.photo)
        
        # Обработка текста
        self.dp.message.register(self.handle_text, F.text)
        
        # Обработка callback запросов
        self.dp.callback_query.register(self.handle_callback)
    
    async def cmd_start(self, message: types.Message):
        """Обработчик команды /start"""
        welcome_text = """
📸 **Добро пожаловать в Photo Advice Bot!**

Я помогу вам улучшить ваши фотографии, дам советы по композиции, освещению и технике съемки.

**📷 Как пользоваться:**
• Отправьте фото для анализа
• Получите детальные советы по улучшению
• Узнайте о технических аспектах съемки

**🔍 Команды:**
/help - помощь
/reset - начать заново

**Примеры советов:**
• Композиция и правило третей
• Настройки камеры
• Освещение и экспозиция
• Постобработка
        """
        
        await message.answer(welcome_text)
    
    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help"""
        help_text = """
🆘 **Помощь по использованию бота**

**📸 Анализ фото:**
• Отправьте любое фото
• Бот проанализирует композицию, освещение, технику
• Получите конкретные советы по улучшению

**🎯 Типы советов:**
• Композиция (правило третей, симметрия, линии)
• Освещение (контраст, тени, цветовая температура)
• Техника (резкость, глубина резкости, экспозиция)
• Постобработка (цветокоррекция, контраст, насыщенность)

**💡 Дополнительные функции:**
• Анализ настроения фото
• Рекомендации по стилю
• Советы по улучшению
        """
        
        await message.answer(help_text)
    
    async def cmd_reset(self, message: types.Message):
        """Обработчик команды /reset"""
        session = self.session_store.get_session(message.from_user.id)
        session.reset_photo_state()
        
        await message.answer("✅ Готово! Отправьте новое фото для анализа.")
    
    async def handle_photo(self, message: types.Message):
        """Обработчик фото"""
        try:
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
            
            # Изменяем размер если нужно
            image_data = FileUtils.resize_image_if_needed(image_data)
            
            # Анализируем фото
            await message.answer("🔍 Анализирую фото...")
            
            analysis_result = await self.analyzer.analyze_photo(image_data)
            
            if not analysis_result:
                await message.answer("❌ Не удалось проанализировать фото. Попробуйте другое фото.")
                return
            
            # Формируем текстовый ответ
            advice_text = self._format_advice_text(analysis_result)
            
            # Создаем карточку с советами
            card_data = self.renderer.render_advice_card(analysis_result)
            
            # Отправляем результат
            await message.answer_photo(
                photo=InputFile(BytesIO(card_data), filename="photo_advice.png"),
                caption=advice_text
            )
            
            # Создаем клавиатуру с дополнительными действиями
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text="💡 Еще советы",
                callback_data="more_advice"
            ))
            keyboard.add(InlineKeyboardButton(
                text="🎨 Стиль",
                callback_data="style_advice"
            ))
            keyboard.add(InlineKeyboardButton(
                text="📷 Техника",
                callback_data="technical_advice"
            ))
            keyboard.add(InlineKeyboardButton(
                text="🔄 Новый анализ",
                callback_data="new_analysis"
            ))
            
            keyboard.adjust(2)
            
            await message.answer(
                "🎉 Анализ завершен! Что хотите узнать еще?",
                reply_markup=keyboard.as_markup()
            )
            
            # Сохраняем в сессию
            session = self.session_store.get_session(message.from_user.id)
            session.current_photo_analysis = analysis_result
            session.add_advice_shown(analysis_result.main_advice)
        
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await message.answer("❌ Ошибка анализа фото. Попробуйте еще раз.")
    
    async def handle_text(self, message: types.Message):
        """Обработчик текстовых сообщений"""
        text = message.text.strip().lower()
        
        if text in ['совет', 'советы', 'помощь', 'help']:
            await self.cmd_help(message)
        elif text in ['сброс', 'reset', 'новый', 'заново']:
            await self.cmd_reset(message)
        else:
            await message.answer(
                "📸 Отправьте фото для анализа или используйте команды:\n"
                "/help - помощь\n"
                "/reset - начать заново"
            )
    
    def _format_advice_text(self, analysis_result) -> str:
        """Форматирует текст с советами"""
        text = f"📸 **Анализ фотографии**\n\n"
        
        # Основной совет
        text += f"💡 **Главный совет:**\n{analysis_result.main_advice}\n\n"
        
        # Оценки
        text += f"📊 **Оценки:**\n"
        text += f"• Композиция: {analysis_result.composition_score}/10\n"
        text += f"• Освещение: {analysis_result.lighting_score}/10\n"
        text += f"• Техника: {analysis_result.technical_score}/10\n"
        text += f"• Общая оценка: {analysis_result.overall_score}/10\n\n"
        
        # Дополнительные советы
        if analysis_result.additional_advice:
            text += f"🔧 **Дополнительные советы:**\n"
            for advice in analysis_result.additional_advice[:3]:
                text += f"• {advice}\n"
        
        return text
    
    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик callback запросов"""
        await callback.answer()
        
        data = callback.data
        session = self.session_store.get_session(callback.from_user.id)
        
        if data == "more_advice":
            # Дополнительные советы
            if not session.current_photo_analysis:
                await callback.message.answer("❌ Сначала проанализируйте фото.")
                return
            
            try:
                additional_advice = await self.analyzer.get_additional_advice(
                    session.current_photo_analysis
                )
                
                if additional_advice:
                    advice_text = "💡 **Дополнительные советы:**\n\n"
                    for advice in additional_advice:
                        advice_text += f"• {advice}\n"
                    
                    await callback.message.answer(advice_text)
                else:
                    await callback.message.answer("😔 Больше советов не найдено.")
            
            except Exception as e:
                logger.error(f"Ошибка получения дополнительных советов: {e}")
                await callback.message.answer("❌ Ошибка получения советов. Попробуйте позже.")
        
        elif data == "style_advice":
            # Советы по стилю
            await callback.message.answer(
                "🎨 **Советы по стилю фотографии:**\n\n"
                "• Используйте правило третей для композиции\n"
                "• Экспериментируйте с углами съемки\n"
                "• Обращайте внимание на цветовую гармонию\n"
                "• Создавайте глубину с помощью переднего плана\n"
                "• Используйте симметрию для статичных сцен"
            )
        
        elif data == "technical_advice":
            # Технические советы
            await callback.message.answer(
                "📷 **Технические советы:**\n\n"
                "• Проверьте резкость перед съемкой\n"
                "• Используйте штатив для стабилизации\n"
                "• Настройте баланс белого\n"
                "• Экспериментируйте с выдержкой и диафрагмой\n"
                "• Снимайте в RAW для лучшего качества"
            )
        
        elif data == "new_analysis":
            # Новый анализ
            session.reset_photo_state()
            await callback.message.answer("✅ Готово! Отправьте новое фото для анализа.")
    
    async def start_polling(self):
        """Запускает бота в режиме polling"""
        try:
            # Очистка истекших сессий каждые 5 минут
            asyncio.create_task(self._cleanup_sessions_periodically())
            
            logger.info("Запуск бота в режиме polling...")
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
        bot = PhotoAdviceBot()
        await bot.start_polling()
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
