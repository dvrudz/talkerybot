#!/usr/bin/env python
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Проверка наличия токена
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("Ошибка: BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

# Создаем роутер
router = Router()

# Классы клавиатур
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def language_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🇬🇧 Английский"), KeyboardButton("🇩🇪 Немецкий"))
    return keyboard

def level_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("A1"), KeyboardButton("A2"))
    keyboard.add(KeyboardButton("B1"), KeyboardButton("B2"))
    return keyboard

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Изучать новые слова"))
    keyboard.add(KeyboardButton("🔄 Тренировка"), KeyboardButton("📋 Мои слова"))
    keyboard.add(KeyboardButton("📊 Мой прогресс"), KeyboardButton("⚙️ Настройки"))
    return keyboard

# Классы состояний
class RegistrationForm(StatesGroup):
    name = State()
    language = State()
    level = State()

# Обработчики команд и сообщений
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start. Проверяет, существует ли пользователь, если нет - начинает регистрацию.
    """
    try:
        # Начать регистрацию
        await message.answer(
            "Добро пожаловать в TalkeryBot - ваш помощник в изучении языков! 🎓\n\n"
            "Давайте настроим ваш профиль. Как вас зовут?"
        )
        await state.set_state(RegistrationForm.name)
        logger.info(f"Начата регистрация пользователя: {message.from_user.id}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

@router.message(RegistrationForm.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Обработчик ввода имени при регистрации.
    """
    try:
        await state.update_data(name=message.text)
        
        await message.answer(
            f"Приятно познакомиться, {message.text}!\n\n"
            "Какой язык вы хотите изучать?",
            reply_markup=language_keyboard()
        )
        await state.set_state(RegistrationForm.language)
        logger.info(f"Пользователь {message.from_user.id} ввел имя: {message.text}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике process_name: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@router.message(RegistrationForm.language)
async def process_language(message: types.Message, state: FSMContext):
    """
    Обработчик выбора языка при регистрации.
    """
    try:
        if message.text in ["🇬🇧 Английский", "🇩🇪 Немецкий"]:
            language = "english" if message.text == "🇬🇧 Английский" else "german"
            await state.update_data(language=language)
            
            await message.answer(
                f"Отлично! Вы выбрали изучение {message.text.lower().replace('🇬🇧 ', '').replace('🇩🇪 ', '')}.\n\n"
                "Теперь выберите ваш текущий уровень:",
                reply_markup=level_keyboard()
            )
            await state.set_state(RegistrationForm.level)
            logger.info(f"Пользователь {message.from_user.id} выбрал язык: {language}")
        else:
            await message.answer(
                "Пожалуйста, выберите язык, используя кнопки ниже.",
                reply_markup=language_keyboard()
            )
    except Exception as e:
        logger.exception(f"Ошибка в обработчике process_language: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@router.message(RegistrationForm.level)
async def process_level(message: types.Message, state: FSMContext):
    """
    Обработчик выбора уровня при регистрации.
    """
    try:
        if message.text in ["A1", "A2", "B1", "B2"]:
            user_data = await state.get_data()
            name = user_data["name"]
            language = user_data["language"]
            level = message.text
            
            # Здесь будет создание пользователя в базе данных
            # (просто выводим сообщение об успешной регистрации для отладки)
            
            await message.answer(
                f"Отлично! Ваш профиль создан.\n\n"
                f"• Имя: {name}\n"
                f"• Язык: {language}\n"
                f"• Уровень: {level}\n\n"
                f"Все готово! Начнем изучение 🚀",
                reply_markup=main_menu_keyboard()
            )
            
            # Очищаем состояние
            await state.clear()
            logger.info(f"Пользователь {message.from_user.id} успешно зарегистрирован")
        else:
            await message.answer(
                "Пожалуйста, выберите уровень, используя кнопки ниже.",
                reply_markup=level_keyboard()
            )
    except Exception as e:
        logger.exception(f"Ошибка в обработчике process_level: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

# Запуск бота
async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
