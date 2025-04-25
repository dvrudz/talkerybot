#!/usr/bin/env python
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
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

# Простая клавиатура для демонстрации
def demo_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🇬🇧 Английский"), KeyboardButton("🇩🇪 Немецкий"))
    keyboard.add(KeyboardButton("Помощь"), KeyboardButton("О боте"))
    return keyboard

# Обработчики команд
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start.
    """
    try:
        await message.answer(
            "Добро пожаловать в TalkeryBot - ваш помощник в изучении языков! 🎓\n\n"
            "Я работаю в упрощенном режиме. Выберите опцию из меню:",
            reply_markup=demo_keyboard()
        )
        logger.info(f"Отправлено приветствие пользователю: {message.from_user.id}")
    except Exception as e:
        logger.exception(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "Справка по использованию бота:\n"
        "• /start - начать работу с ботом\n"
        "• /help - показать эту справку\n"
        "• /about - информация о боте\n"
    )
    logger.info(f"Отправлена справка пользователю: {message.from_user.id}")

@router.message(Command("about"))
async def cmd_about(message: types.Message):
    """Обработчик команды /about"""
    await message.answer(
        "О боте TalkeryBot:\n\n"
        "Версия: 1.0.0\n"
        "Создатель: @dvrudz\n\n"
        "Бот предназначен для изучения иностранных языков с помощью технологии интервальных повторений."
    )
    logger.info(f"Отправлена информация о боте пользователю: {message.from_user.id}")

# Обработчик текстовых сообщений
@router.message()
async def echo_message(message: types.Message):
    """Эхо-обработчик для любых текстовых сообщений"""
    try:
        if message.text == "Помощь":
            await cmd_help(message)
        elif message.text == "О боте":
            await cmd_about(message)
        elif message.text in ["🇬🇧 Английский", "🇩🇪 Немецкий"]:
            language = "английский" if message.text == "🇬🇧 Английский" else "немецкий"
            await message.answer(
                f"Вы выбрали {language} язык.\n"
                f"В настоящий момент бот работает в демонстрационном режиме."
            )
            logger.info(f"Пользователь {message.from_user.id} выбрал язык: {language}")
        else:
            await message.answer(
                "Я не понимаю такую команду.\n"
                "Используйте кнопки или введите /help для справки.",
                reply_markup=demo_keyboard()
            )
    except Exception as e:
        logger.exception(f"Ошибка при обработке сообщения: {e}")
        await message.answer("Произошла ошибка при обработке сообщения.")

# Функция для удаления webhook перед запуском
async def delete_webhook():
    """Удаляет webhook если он установлен"""
    try:
        bot_temp = Bot(token=BOT_TOKEN)
        # Принудительно удаляем вебхук
        await bot_temp.delete_webhook(drop_pending_updates=True)
        # Проверяем результат
        info = await bot_temp.get_webhook_info()
        logger.info(f"Webhook удален: {info.url is None}")
        
        # Закрываем сессию
        await bot_temp.session.close()
        
        # Добавляем задержку после удаления webhook
        logger.info("Ожидаем 3 секунды для стабилизации после удаления webhook")
        await asyncio.sleep(3)
    except Exception as e:
        logger.error(f"Ошибка при удалении webhook: {e}")

# Запуск бота
async def main():
    # Удаляем webhook перед запуском бота
    await delete_webhook()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Запуск бота
    await dp.start_polling(bot, skip_updates=True)

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
    
    logger.info("Запуск бота...")
    asyncio.run(main())
