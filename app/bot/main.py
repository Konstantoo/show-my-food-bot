import asyncio
import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import Config
from app.core.analyzer import DishAnalyzer
from app.core.renderer import CardRenderer
from app.core.session import SessionStore
from app.utils.text_parse import TextParser
from app.utils.file_utils import FileUtils
from app.core.rules import ValidationRules, BusinessRules

# Настройка логирования
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Состояния FSM
class DishAnalysisStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_weight = State()
    waiting_for_cooking_method = State()
    waiting_for_correction = State()


class ShowMyFoodBot:
    """Основной класс Telegram бота"""
    
    def __init__(self):
        # Инициализация компонентов
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.session_store = SessionStore()
        self.analyzer = DishAnalyzer()
        self.renderer = CardRenderer()
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_privacy, Command("privacy"))
        self.dp.message.register(self.cmd_reset, Command("reset"))
        self.dp.message.register(self.cmd_fact, Command("fact"))
        
        # Обработка фото
        self.dp.message.register(self.handle_photo, F.photo)
        
        # Обработка текста
        self.dp.message.register(self.handle_text, F.text)
        
        # Обработка callback запросов
        self.dp.callback_query.register(self.handle_callback)
    
    async def cmd_start(self, message: types.Message):
        """Обработчик команды /start"""
        welcome_text = """
🍽️ Добро пожаловать в Show My Food Bot!

Я помогу вам узнать калорийность и интересные факты о ваших блюдах.

📸 **Как пользоваться:**
1. Отправьте фото блюда
2. Подтвердите название или уточните детали
3. Получите карточку с калориями и фактами!

🔍 **Доступные команды:**
/help - помощь
/privacy - политика конфиденциальности
/reset - сбросить текущий анализ
/fact - получить еще один факт

**Пример фото:** любое блюдо - паста, суп, салат, пицца и т.д.
        """
        
        await message.answer(welcome_text)
    
    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help"""
        help_text = """
🆘 **Помощь по использованию бота**

📸 **Анализ фото:**
• Отправьте фото блюда
• Бот предложит варианты названий
• Подтвердите или уточните детали

⚖️ **Уточнение веса:**
• Укажите вес в граммах (например: "250г")
• По умолчанию используется 200г

👨‍🍳 **Способ приготовления:**
• варка, жарка, запекание, тушение, гриль
• Влияет на калорийность

💡 **Факты:**
• История блюда
• Интересные детали об ингредиентах
• События и традиции
• Упоминания знаменитостей (только проверенные)

🔧 **Команды:**
/reset - начать новый анализ
/fact - получить дополнительный факт
/privacy - политика конфиденциальности
        """
        
        await message.answer(help_text)
    
    async def cmd_privacy(self, message: types.Message):
        """Обработчик команды /privacy"""
        privacy_text = """
🔒 **Политика конфиденциальности**

**Обработка данных:**
• Фото обрабатываются в памяти и не сохраняются
• Сессия хранится 30 минут, затем удаляется
• Никакие персональные данные не передаются третьим лицам

**Используемые сервисы:**
• Perplexity AI - для получения фактов о блюдах
• Локальная база данных - для расчета калорий

**Безопасность:**
• Все данные обрабатываются локально
• Фото удаляются сразу после анализа
• История чата не сохраняется

**Контакты:**
По вопросам конфиденциальности обращайтесь к администратору бота.
        """
        
        await message.answer(privacy_text)
    
    async def cmd_reset(self, message: types.Message):
        """Обработчик команды /reset"""
        session = self.session_store.get_session(message.from_user.id)
        session.reset_dish_state()
        
        await message.answer("✅ Анализ сброшен. Можете отправить новое фото!")
    
    async def cmd_fact(self, message: types.Message):
        """Обработчик команды /fact"""
        session = self.session_store.get_session(message.from_user.id)
        
        if not session.current_dish:
            await message.answer("❌ Сначала проанализируйте блюдо, отправив фото.")
            return
        
        # Получаем дополнительный факт
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
                
                await message.answer(fact_text)
            else:
                # Пробуем получить резервный факт
                fallback_facts = await self.analyzer.get_fallback_facts(session.get_exclude_facts())
                if fallback_facts:
                    fact = fallback_facts[0]
                    session.add_fact_shown(fact.text)
                    
                    fact_text = f"💡 **{fact.type.title()}**\n\n{fact.text}"
                    if fact.sources:
                        sources_text = TextParser.format_sources(fact.sources)
                        fact_text += f"\n\n🔗 Источник: {sources_text}"
                    
                    await message.answer(fact_text)
                else:
                    await message.answer("😔 Больше фактов не найдено. Попробуйте другое блюдо!")
        
        except Exception as e:
            logger.error(f"Ошибка получения факта: {e}")
            await message.answer("❌ Ошибка получения факта. Попробуйте позже.")
    
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
            
            suggestions = await self.analyzer.get_dish_suggestions(image_data)
            
            if not suggestions:
                await message.answer("❌ Не удалось распознать блюдо на фото. Попробуйте другое фото.")
                return
            
            # Сохраняем в сессию
            session = self.session_store.get_session(message.from_user.id)
            session.current_dish = suggestions[0]
            session.waiting_for_confirmation = True
            
            # Создаем клавиатуру с вариантами
            keyboard = InlineKeyboardBuilder()
            for i, suggestion in enumerate(suggestions[:3]):
                keyboard.add(InlineKeyboardButton(
                    text=f"✅ {suggestion.title()}",
                    callback_data=f"confirm_dish_{i}"
                ))
            
            keyboard.add(InlineKeyboardButton(
                text="✏️ Уточнить название",
                callback_data="correct_dish"
            ))
            
            keyboard.adjust(1)
            
            suggestions_text = "🍽️ **Распознанные блюда:**\n\n"
            for i, suggestion in enumerate(suggestions[:3]):
                suggestions_text += f"{i+1}. {suggestion.title()}\n"
            
            suggestions_text += "\nВыберите правильный вариант или уточните название:"
            
            await message.answer(
                suggestions_text,
                reply_markup=keyboard.as_markup()
            )
        
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await message.answer("❌ Ошибка анализа фото. Попробуйте еще раз.")
    
    async def handle_text(self, message: types.Message):
        """Обработчик текстовых сообщений"""
        session = self.session_store.get_session(message.from_user.id)
        text = message.text.strip()
        
        # Если ждем подтверждения блюда
        if session.waiting_for_confirmation:
            await self._handle_dish_confirmation(message, text)
        # Если ждем уточнения веса
        elif session.waiting_for_weight:
            await self._handle_weight_input(message, text)
        # Если ждем способ приготовления
        elif session.waiting_for_cooking_method:
            await self._handle_cooking_method_input(message, text)
        # Если ждем исправления названия
        elif session.waiting_for_correction:
            await self._handle_dish_correction(message, text)
        else:
            # Пытаемся распарсить как описание блюда
            await self._handle_dish_description(message, text)
    
    async def _handle_dish_confirmation(self, message: types.Message, text: str):
        """Обработка подтверждения блюда"""
        session = self.session_store.get_session(message.from_user.id)
        
        # Парсим описание блюда
        dish_name, weight, cooking_method = TextParser.parse_dish_description(text)
        
        if not ValidationRules.validate_dish_name(dish_name):
            await message.answer("❌ Неверное название блюда. Попробуйте еще раз.")
            return
        
        session.current_dish = dish_name
        session.current_weight = weight
        session.current_cooking_method = cooking_method
        session.waiting_for_confirmation = False
        
        # Запускаем анализ
        await self._perform_full_analysis(message, session)
    
    async def _handle_weight_input(self, message: types.Message, text: str):
        """Обработка ввода веса"""
        session = self.session_store.get_session(message.from_user.id)
        
        weight = TextParser.extract_weight(text)
        if not weight or not ValidationRules.validate_weight(weight):
            await message.answer("❌ Неверный вес. Укажите вес в граммах (например: 250г)")
            return
        
        session.current_weight = weight
        session.waiting_for_weight = False
        
        # Запускаем анализ
        await self._perform_full_analysis(message, session)
    
    async def _handle_cooking_method_input(self, message: types.Message, text: str):
        """Обработка ввода способа приготовления"""
        session = self.session_store.get_session(message.from_user.id)
        
        cooking_method = TextParser.extract_cooking_method(text)
        if not ValidationRules.validate_cooking_method(cooking_method):
            await message.answer("❌ Неверный способ приготовления. Доступные: варка, жарка, запекание, тушение, гриль")
            return
        
        session.current_cooking_method = cooking_method
        session.waiting_for_cooking_method = False
        
        # Запускаем анализ
        await self._perform_full_analysis(message, session)
    
    async def _handle_dish_correction(self, message: types.Message, text: str):
        """Обработка исправления названия блюда"""
        session = self.session_store.get_session(message.from_user.id)
        
        dish_name = TextParser.clean_dish_name(text)
        if not ValidationRules.validate_dish_name(dish_name):
            await message.answer("❌ Неверное название блюда. Попробуйте еще раз.")
            return
        
        session.current_dish = dish_name
        session.waiting_for_correction = False
        
        # Спрашиваем вес
        session.waiting_for_weight = True
        await message.answer(f"🍽️ Блюдо: {dish_name.title()}\n\n⚖️ Укажите вес в граммах (например: 250г):")
    
    async def _handle_dish_description(self, message: types.Message, text: str):
        """Обработка описания блюда без фото"""
        # Парсим описание
        dish_name, weight, cooking_method = TextParser.parse_dish_description(text)
        
        if not ValidationRules.validate_dish_name(dish_name):
            await message.answer("❌ Не удалось распознать блюдо. Отправьте фото или уточните название.")
            return
        
        # Сохраняем в сессию
        session = self.session_store.get_session(message.from_user.id)
        session.current_dish = dish_name
        session.current_weight = weight
        session.current_cooking_method = cooking_method
        
        # Запускаем анализ
        await self._perform_full_analysis(message, session)
    
    async def _perform_full_analysis(self, message: types.Message, session):
        """Выполняет полный анализ блюда"""
        try:
            await message.answer("🔄 Анализирую блюдо...")
            
            # Получаем ингредиенты
            ingredients = await self.analyzer.get_ingredients_for_dish(session.current_dish)
            session.current_ingredients = ingredients
            
            # Выполняем полный анализ
            nutrition_result, facts_result = await self.analyzer.full_analysis(
                session.current_dish,
                session.current_weight,
                session.current_cooking_method,
                session.get_exclude_facts()
            )
            
            if not nutrition_result:
                await message.answer("❌ Не удалось найти информацию о питательной ценности этого блюда.")
                return
            
            # Сохраняем результат
            session.nutrition_result = nutrition_result
            
            # Формируем текстовый ответ
            nutrition_text = TextParser.format_nutrition_text(nutrition_result)
            
            # Добавляем факты
            if facts_result.facts:
                fact = facts_result.facts[0]
                session.add_fact_shown(fact.text)
                
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
                text="👨‍🍳 Изменить способ",
                callback_data="change_cooking"
            ))
            
            keyboard.adjust(1)
            
            await message.answer(
                "🎉 Анализ завершен! Что хотите сделать дальше?",
                reply_markup=keyboard.as_markup()
            )
        
        except Exception as e:
            logger.error(f"Ошибка анализа блюда: {e}")
            await message.answer("❌ Ошибка анализа. Попробуйте еще раз.")
    
    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик callback запросов"""
        await callback.answer()
        
        data = callback.data
        session = self.session_store.get_session(callback.from_user.id)
        
        if data.startswith("confirm_dish_"):
            # Подтверждение блюда
            index = int(data.split("_")[-1])
            suggestions = await self.analyzer.get_dish_suggestions(b"")  # Получаем из сессии
            
            if index < len(suggestions):
                session.current_dish = suggestions[index]
                session.waiting_for_confirmation = False
                session.waiting_for_weight = True
                
                await callback.message.edit_text(
                    f"🍽️ Блюдо: {suggestions[index].title()}\n\n⚖️ Укажите вес в граммах (например: 250г):"
                )
        
        elif data == "correct_dish":
            # Исправление названия
            session.waiting_for_confirmation = False
            session.waiting_for_correction = True
            
            await callback.message.edit_text("✏️ Введите правильное название блюда:")
        
        elif data == "more_fact":
            # Дополнительный факт
            await self.cmd_fact(callback.message)
        
        elif data == "change_weight":
            # Изменение веса
            session.waiting_for_weight = True
            await callback.message.edit_text("⚖️ Укажите новый вес в граммах:")
        
        elif data == "change_cooking":
            # Изменение способа приготовления
            session.waiting_for_cooking_method = True
            await callback.message.edit_text("👨‍🍳 Укажите способ приготовления (варка, жарка, запекание, тушение, гриль):")
    
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
        bot = ShowMyFoodBot()
        await bot.start_polling()
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
