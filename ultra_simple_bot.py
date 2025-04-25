#!/usr/bin/env python
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
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

# Функция для создания клавиатуры
def get_main_keyboard():
    """Создает основную клавиатуру бота"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🇬🇧 Английский"), KeyboardButton("🇩🇪 Немецкий"))
    kb.add(KeyboardButton("ℹ️ Помощь"), KeyboardButton("🔍 О боте"))
    return kb

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start.
    """
    try:
        # Создаем клавиатуру
        keyboard = get_main_keyboard()
        logger.info(f"Клавиатура создана для пользователя {message.from_user.id}")
        
        # Отправляем приветствие с клавиатурой
        await message.answer(
            "Привет! Я простой тестовый бот с клавиатурой.\nВыберите опцию или используйте /help для справки.",
            reply_markup=keyboard
        )
        logger.info(f"Отправлено приветствие пользователю: {message.from_user.id}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    try:
        keyboard = get_main_keyboard()
        await message.answer(
            "Базовые команды:\n"
            "• /start - начать работу с ботом\n"
            "• /help - показать эту справку\n"
            "• /ping - проверить работу бота\n",
            reply_markup=keyboard
        )
        logger.info(f"Отправлена справка пользователю: {message.from_user.id}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике help: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

@router.message(Command("ping"))
async def cmd_ping(message: types.Message):
    """Обработчик команды /ping"""
    try:
        await message.answer("Pong! Бот работает нормально.")
        logger.info(f"Отправлен pong пользователю: {message.from_user.id}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике ping: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

# Обработчик текстовых сообщений
@router.message()
async def echo(message: types.Message):
    """Обработчик для любых текстовых сообщений"""
    try:
        # Обрабатываем кнопки клавиатуры
        if message.text == "ℹ️ Помощь":
            return await cmd_help(message)
        elif message.text == "🔍 О боте":
            await message.answer(
                "О боте TalkeryBot:\n\n"
                "Версия: 1.0.0\n"
                "Бот для изучения иностранных языков"
            )
            logger.info(f"Отправлена информация о боте пользователю: {message.from_user.id}")
            return
        elif message.text in ["🇬🇧 Английский", "🇩🇪 Немецкий"]:
            language = "английский" if message.text == "🇬🇧 Английский" else "немецкий"
            await message.answer(
                f"Вы выбрали {language} язык.\n"
                f"В настоящий момент бот работает в демонстрационном режиме."
            )
            logger.info(f"Пользователь {message.from_user.id} выбрал язык: {language}")
            return
            
        # Стандартное эхо для других сообщений
        await message.answer(f"Вы написали: {message.text}", reply_markup=get_main_keyboard())
        logger.info(f"Эхо для пользователя {message.from_user.id}: {message.text}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике сообщений: {e}")
        await message.answer("Произошла ошибка при обработке сообщения.")

# Функция для удаления webhook перед запуском
async def delete_webhook():
    """Удаляет webhook если он установлен"""
    try:
        logger.info("Удаление вебхука...")
        bot_temp = Bot(token=BOT_TOKEN)
        await bot_temp.delete_webhook(drop_pending_updates=True)
        info = await bot_temp.get_webhook_info()
        logger.info(f"Webhook удален: {info.url is None}")
        await bot_temp.session.close()
    except Exception as e:
        logger.error(f"Ошибка при удалении webhook: {e}")

# Запуск бота
async def main():
    # Удаляем webhook перед запуском бота
    await delete_webhook()
    
    # Инициализация бота и диспетчера
    logger.info("Инициализация бота...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Запуск бота
    logger.info("Запуск поллинга...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    # Запускаем простой HTTP сервер для Render.com
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
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    logger.info("Запуск бота...")
    asyncio.run(main())
