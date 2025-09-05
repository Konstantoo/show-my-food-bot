import asyncio
import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import Config
from app.core.analyzer_refactored import DishAnalyzerRefactored
from app.core.renderer_refactored import CardRendererRefactored
from app.core.session import SessionStore
from app.utils.text_parse import TextParser
from app.utils.file_utils import FileUtils

# Настройка логирования
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


class ShowMyFoodBotRefactored:
    """Упрощенная версия Telegram бота для анализа блюд"""
    
    def __init__(self):
        # Инициализация компонентов
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.session_store = SessionStore()
        self.analyzer = DishAnalyzerRefactored()
        self.renderer = CardRendererRefactored()
        
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
🍽️ **Добро пожаловать в Show My Food Bot!**

Я помогу вам узнать калорийность и интересные факты о ваших блюдах.

**📸 Как пользоваться:**
• Отправьте фото блюда
• Или напишите название блюда
• Получите красивую карточку с калориями!

**🔍 Команды:**
/help - помощь
/reset - начать заново

**Примеры:**
• Фото пасты → анализ с калориями
• "борщ 300г" → расчет калорий
• "пицца" → стандартный анализ
        """
        
        await message.answer(welcome_text)
    
    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help"""
        help_text = """
🆘 **Помощь по использованию бота**

**📸 Анализ фото:**
• Отправьте фото блюда
• Бот автоматически определит блюдо
• Получите карточку с калориями

**📝 Текстовый ввод:**
• "название блюда" - стандартный анализ (200г)
• "название 300г" - с указанием веса
• "название 250г жарка" - с весом и способом

**⚖️ Вес (опционально):**
• По умолчанию: 200г
• Форматы: "250г", "250 г", "250g"

**👨‍🍳 Способы приготовления:**
• варка (по умолчанию)
• жарка, запекание, тушение, гриль

**💡 Факты:**
• История блюда
• Интересные детали
• Проверенные источники
        """
        
        await message.answer(help_text)
    
    async def cmd_reset(self, message: types.Message):
        """Обработчик команды /reset"""
        session = self.session_store.get_session(message.from_user.id)
        session.reset_dish_state()
        
        await message.answer("✅ Готово! Отправьте новое фото или название блюда.")
    
    async def handle_photo(self, message: types.Message):
        """Обработчик фото - упрощенная версия"""
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
            
            suggestions = await self.analyzer.get_dish_suggestions(image_data)
            
            if not suggestions:
                await message.answer("❌ Не удалось распознать блюдо на фото. Попробуйте другое фото или напишите название блюда.")
                return
            
            # Берем первое предложение и сразу анализируем
            dish_name = suggestions[0]
            await self._analyze_dish(message, dish_name, 200, "варка")
        
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await message.answer("❌ Ошибка анализа фото. Попробуйте еще раз.")
    
    async def handle_text(self, message: types.Message):
        """Обработчик текстовых сообщений - упрощенная версия"""
        text = message.text.strip()
        
        # Парсим описание блюда
        dish_name, weight, cooking_method = TextParser.parse_dish_description(text)
        
        if not dish_name:
            await message.answer("❌ Не удалось распознать блюдо. Попробуйте еще раз или отправьте фото.")
            return
        
        # Используем значения по умолчанию если не указаны
        weight = weight or 200
        cooking_method = cooking_method or "варка"
        
        await self._analyze_dish(message, dish_name, weight, cooking_method)
    
    async def _analyze_dish(self, message: types.Message, dish_name: str, weight: int, cooking_method: str):
        """Выполняет анализ блюда и отправляет результат"""
        try:
            await message.answer("🔄 Анализирую блюдо...")
            
            # Получаем ингредиенты
            ingredients = await self.analyzer.get_ingredients_for_dish(dish_name)
            
            # Выполняем полный анализ
            nutrition_result, facts_result = await self.analyzer.full_analysis(
                dish_name,
                weight,
                cooking_method,
                []
            )
            
            if not nutrition_result:
                await message.answer(f"❌ Не удалось найти информацию о блюде '{dish_name}'. Попробуйте другое название.")
                return
            
            # Формируем текстовый ответ
            nutrition_text = self._format_nutrition_text(nutrition_result)
            
            # Добавляем факт если есть
            if facts_result.facts:
                fact = facts_result.facts[0]
                fact_text = f"\n\n💡 **{fact.type.title()}**\n{fact.text}"
                if fact.sources:
                    sources_text = TextParser.format_sources(fact.sources)
                    fact_text += f"\n\n🔗 Источник: {sources_text}"
                
                nutrition_text += fact_text
            
            # Создаем карточку
            card_data = self.renderer.render_card(nutrition_result, facts_result.facts)
            
            # Отправляем результат
            await message.answer_photo(
                photo=InputFile(BytesIO(card_data), filename="dish_card.png"),
                caption=nutrition_text
            )
            
            # Создаем клавиатуру с дополнительными действиями
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text="💡 Еще факт",
                callback_data="more_fact"
            ))
            keyboard.add(InlineKeyboardButton(
                text="⚖️ Изменить вес",
                callback_data="change_weight"
            ))
            keyboard.add(InlineKeyboardButton(
                text="🔄 Новый анализ",
                callback_data="new_analysis"
            ))
            
            keyboard.adjust(1)
            
            await message.answer(
                "🎉 Анализ завершен! Что хотите сделать дальше?",
                reply_markup=keyboard.as_markup()
            )
            
            # Сохраняем в сессию
            session = self.session_store.get_session(message.from_user.id)
            session.current_dish = dish_name
            session.current_weight = weight
            session.current_cooking_method = cooking_method
            session.nutrition_result = nutrition_result
            if facts_result.facts:
                session.add_fact_shown(facts_result.facts[0].text)
        
        except Exception as e:
            logger.error(f"Ошибка анализа блюда: {e}")
            await message.answer("❌ Ошибка анализа. Попробуйте еще раз.")
    
    def _format_nutrition_text(self, nutrition_result) -> str:
        """Форматирует текст с информацией о питательной ценности"""
        text = f"🍽️ **{nutrition_result.dish_name.title()}**\n"
        text += f"⚖️ Вес: {nutrition_result.weight_g}г\n"
        text += f"👨‍🍳 Способ: {nutrition_result.cooking_method}\n\n"
        
        text += f"🔥 **{nutrition_result.total_kcal} ккал**\n"
        text += f"🥩 Белки: {nutrition_result.total_protein}г\n"
        text += f"🥓 Жиры: {nutrition_result.total_fat}г\n"
        text += f"🍞 Углеводы: {nutrition_result.total_carbs}г\n"
        
        if nutrition_result.assumptions:
            text += f"\n📝 *{', '.join(nutrition_result.assumptions)}*"
        
        return text
    
    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик callback запросов"""
        await callback.answer()
        
        data = callback.data
        session = self.session_store.get_session(callback.from_user.id)
        
        if data == "more_fact":
            # Дополнительный факт
            if not session.current_dish:
                await callback.message.answer("❌ Сначала проанализируйте блюдо.")
                return
            
            try:
                facts_result = await self.analyzer.get_facts(
                    session.current_dish,
                    session.current_ingredients,
                    session.get_exclude_facts()
                )
                
                if facts_result.facts:
                    fact = facts_result.facts[0]
                    session.add_fact_shown(fact.text)
                    
                    fact_text = f"💡 **{fact.type.title()}**\n\n{fact.text}"
                    if fact.sources:
                        sources_text = TextParser.format_sources(fact.sources)
                        fact_text += f"\n\n🔗 Источник: {sources_text}"
                    
                    await callback.message.answer(fact_text)
                else:
                    await callback.message.answer("😔 Больше фактов не найдено. Попробуйте другое блюдо!")
            
            except Exception as e:
                logger.error(f"Ошибка получения факта: {e}")
                await callback.message.answer("❌ Ошибка получения факта. Попробуйте позже.")
        
        elif data == "change_weight":
            # Изменение веса
            await callback.message.answer("⚖️ Укажите новый вес в граммах (например: 300г):")
            session.waiting_for_weight = True
        
        elif data == "new_analysis":
            # Новый анализ
            session.reset_dish_state()
            await callback.message.answer("✅ Готово! Отправьте новое фото или название блюда.")
    
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
        bot = ShowMyFoodBotRefactored()
        await bot.start_polling()
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
