#!/usr/bin/env python
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Настройка логирования с более детальным уровнем
logging.basicConfig(
    level=logging.DEBUG,  # Изменено с INFO на DEBUG для получения больше информации
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

# Удаление webhook
async def delete_webhook():
    """Удаляет webhook если он установлен"""
    try:
        bot_temp = Bot(token=BOT_TOKEN)
        await bot_temp.delete_webhook()
        info = await bot_temp.get_webhook_info()
        logger.info(f"Webhook удален: {info.url is None}")
        await bot_temp.session.close()
    except Exception as e:
        logger.error(f"Ошибка при удалении webhook: {e}")

async def start_bot():
    """Запускает бота в режиме long polling"""
    logger.info("Инициализация бота...")
    
    # Сначала удаляем webhook если он установлен
    await delete_webhook()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Добавляем обработчик ошибок
    @dp.errors()
    async def errors_handler(exception):
        logger.exception(f"Ошибка в обработчике: {exception}")
        return True
    
    # Динамический импорт обработчиков
    try:
        logger.info("Импорт обработчиков...")
        
        # Проверяем наличие файлов перед импортом
        import os.path
        handlers_path = 'app/handlers'
        logger.debug(f"Файлы в директории {handlers_path}: {os.listdir(handlers_path) if os.path.exists(handlers_path) else 'Директория не найдена'}")
        
        from app.handlers import registration, menu, learning, training, settings, admin, review
        
        # Выводим информацию о регистрационном обработчике
        logger.debug(f"Регистрационный модуль импортирован: {registration}")
        logger.debug(f"Роутеры в регистрационном модуле: {registration.router}")
        
        from app.database.db import get_session
        
        # Регистрация роутеров
        logger.info("Регистрация роутеров...")
        dp.include_router(registration.router)
        dp.include_router(menu.router)
        dp.include_router(learning.router)
        dp.include_router(training.router)
        dp.include_router(settings.router)
        dp.include_router(admin.router)
        dp.include_router(review.router)
        
        # Middleware для добавления сессии базы данных в хэндлеры
        @dp.update.outer_middleware()
        async def db_session_middleware(handler, event, data):
            logger.debug(f"Обработка обновления: {type(event).__name__}")
            async for session in get_session():
                data["session"] = session
                try:
                    return await handler(event, data)
                except Exception as e:
                    logger.exception(f"Ошибка при обработке события {type(event).__name__}: {e}")
                    raise
    except Exception as e:
        logger.error(f"Ошибка при импорте обработчиков: {e}")
        logger.exception("Трассировка:")
        sys.exit(1)
    
    # Проверка, что бот доступен
    try:
        bot_info = await bot.get_me()
        logger.info(f"Бот успешно подключен: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"Ошибка при проверке доступности бота: {e}")
        sys.exit(1)
    
    # Добавим базовый обработчик для всех сообщений для отладки
    @dp.message()
    async def debug_message_handler(message, bot):
        logger.debug(f"Получено сообщение: {message.text}")
        # Не отвечаем, просто логируем для отладки
    
    # Запуск бота
    logger.info("Запуск бота в режиме polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.exception("Трассировка:")
        sys.exit(1)

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
    
    # Запускаем бота
    logger.info("Запуск TalkeryBot...")
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.exception("Трассировка:")
