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
        logger.info(f"Обработка имени: {message.text} от пользователя {message.from_user.id}")
        
        # Валидация имени (простая проверка)
        if not message.text or len(message.text) > 100:
            await message.answer("Пожалуйста, введите корректное имя (не более 100 символов)")
            return
            
        # Сохраняем имя в состоянии
        await state.update_data(name=message.text)
        logger.info(f"Имя сохранено в состоянии для {message.from_user.id}")
        
        # Отправляем сообщение с клавиатурой выбора языка
        try:
            keyboard = language_keyboard()
            logger.info(f"Клавиатура выбора языка создана для {message.from_user.id}")
            
            await message.answer(
                f"Приятно познакомиться, {message.text}!\n\n"
                "Какой язык вы хотите изучать?",
                reply_markup=keyboard
            )
            logger.info(f"Сообщение с клавиатурой отправлено пользователю {message.from_user.id}")
            
            # Устанавливаем следующее состояние
            await state.set_state(RegistrationForm.language)
            logger.info(f"Установлено состояние RegistrationForm.language для {message.from_user.id}")
        except Exception as keyboard_error:
            logger.exception(f"Ошибка при отправке клавиатуры: {keyboard_error}")
            await message.answer("Произошла ошибка при формировании меню. Пожалуйста, попробуйте команду /start снова.")
            await state.clear()
            return
            
    except Exception as e:
        logger.exception(f"Подробная ошибка в обработчике process_name: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова или напишите /start для перезапуска.")
        # Очищаем состояние при ошибке
        await state.clear()
        
@router.message(RegistrationForm.language)
async def process_language(message: types.Message, state: FSMContext):
    """
    Обработчик выбора языка при регистрации.
    """
    try:
        logger.info(f"Обработка выбора языка: {message.text} от пользователя {message.from_user.id}")
        
        if message.text in ["🇬🇧 Английский", "🇩🇪 Немецкий"]:
            language = "english" if message.text == "🇬🇧 Английский" else "german"
            
            # Сохраняем выбор в состоянии
            await state.update_data(language=language)
            logger.info(f"Язык {language} сохранен в состоянии для {message.from_user.id}")
            
            # Создаем клавиатуру уровней
            keyboard = level_keyboard()
            logger.info(f"Клавиатура выбора уровня создана для {message.from_user.id}")
            
            # Отправляем сообщение с выбором уровня
            await message.answer(
                f"Отлично! Вы выбрали изучение {message.text.lower().replace('🇬🇧 ', '').replace('🇩🇪 ', '')}.\n\n"
                "Теперь выберите ваш текущий уровень:",
                reply_markup=keyboard
            )
            logger.info(f"Сообщение с выбором уровня отправлено пользователю {message.from_user.id}")
            
            # Устанавливаем следующее состояние
            await state.set_state(RegistrationForm.level)
            logger.info(f"Установлено состояние RegistrationForm.level для {message.from_user.id}")
        else:
            await message.answer(
                "Пожалуйста, выберите язык, используя кнопки ниже.",
                reply_markup=language_keyboard()
            )
            logger.info(f"Пользователь {message.from_user.id} ввел некорректный язык: {message.text}")
    except Exception as e:
        logger.exception(f"Подробная ошибка в обработчике process_language: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова или напишите /start для перезапуска.")
        # Очищаем состояние при ошибке
        await state.clear()

@router.message(RegistrationForm.level)
async def process_level(message: types.Message, state: FSMContext):
    """
    Обработчик выбора уровня при регистрации.
    """
    try:
        logger.info(f"Обработка выбора уровня: {message.text} от пользователя {message.from_user.id}")
        
        if message.text in ["A1", "A2", "B1", "B2"]:
            # Получаем сохраненные данные
            user_data = await state.get_data()
            logger.info(f"Получены данные из состояния для {message.from_user.id}: {user_data}")
            
            name = user_data.get("name", "Пользователь")
            language = user_data.get("language", "english")
            level = message.text
            
            # Здесь будет создание пользователя в базе данных
            # (просто выводим сообщение об успешной регистрации для отладки)
            logger.info(f"Регистрация успешна для {message.from_user.id}: имя={name}, язык={language}, уровень={level}")
            
            # Создаем основную клавиатуру
            keyboard = main_menu_keyboard()
            logger.info(f"Основная клавиатура создана для {message.from_user.id}")
            
            await message.answer(
                f"Отлично! Ваш профиль создан.\n\n"
                f"• Имя: {name}\n"
                f"• Язык: {language}\n"
                f"• Уровень: {level}\n\n"
                f"Все готово! Начнем изучение 🚀",
                reply_markup=keyboard
            )
            logger.info(f"Сообщение с подтверждением регистрации отправлено пользователю {message.from_user.id}")
            
            # Очищаем состояние
            await state.clear()
            logger.info(f"Состояние очищено для пользователя {message.from_user.id}")
        else:
            await message.answer(
                "Пожалуйста, выберите уровень, используя кнопки ниже.",
                reply_markup=level_keyboard()
            )
            logger.info(f"Пользователь {message.from_user.id} ввел некорректный уровень: {message.text}")
    except Exception as e:
        logger.exception(f"Подробная ошибка в обработчике process_level: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова или напишите /start для перезапуска.")
        # Очищаем состояние при ошибке
        await state.clear()

# Функция для удаления webhook перед запуском
async def delete_webhook():
    """Удаляет webhook если он установлен"""
    try:
        bot_temp = Bot(token=BOT_TOKEN)
        # Убедимся, что установлено ограничение времени
        await bot_temp.delete_webhook(drop_pending_updates=True)
        # Проверяем результат
        info = await bot_temp.get_webhook_info()
        logger.info(f"Webhook удален: {info.url is None}")
        if info.url is not None:
            logger.warning(f"Webhook не был удален! URL: {info.url}")
            # Повторяем попытку
            await bot_temp.delete_webhook(drop_pending_updates=True)
            info = await bot_temp.get_webhook_info()
            logger.info(f"Повторная попытка удаления webhook: {info.url is None}")
        
        # Закрываем сессию
        await bot_temp.session.close()
        
        # Добавляем задержку после удаления webhook
        logger.info("Ожидаем 5 секунд для стабилизации после удаления webhook")
        await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Ошибка при удалении webhook: {e}")

# Запуск бота
async def main():
    # Удаляем webhook перед запуском бота
    await delete_webhook()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем простой HTTP сервер в отдельном потоке для Render.com
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        
        def log_message(self, format, *args):
            return  # Отключаем логирование HTTP-запросов
    
    # Запуск HTTP сервера в отдельном потоке
    def run_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), SimpleHandler)
        logger.info(f"Запуск HTTP сервера на порту {port}...")
        server.serve_forever()
    
    # Запускаем HTTP сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Завершаем все существующие процессы бота (для Render.com)
    try:
        import psutil
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['pid'] != current_pid and 'python' in proc.info['name'] and 'custom_registration.py' in ' '.join(proc.info.get('cmdline', [])):
                logger.warning(f"Найден другой процесс бота (PID: {proc.info['pid']}), пытаемся завершить")
                try:
                    psutil.Process(proc.info['pid']).terminate()
                    logger.info(f"Процесс {proc.info['pid']} завершен")
                except Exception as e:
                    logger.error(f"Ошибка при завершении процесса {proc.info['pid']}: {e}")
    except ImportError:
        logger.warning("Библиотека psutil не установлена. Невозможно проверить другие процессы.")
    except Exception as e:
        logger.error(f"Ошибка при поиске других процессов: {e}")
    
    # Запускаем бота
    asyncio.run(main())
