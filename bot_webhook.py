#!/usr/bin/env python
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

# Импорт маршрутизаторов и сервисов
from app.handlers import registration, menu, learning, training, settings, admin, review
from app.middlewares.db_session import DatabaseSessionMiddleware
from app.services.notification_service import NotificationService
from app.database.database import get_async_session

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация webhook
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Проверка обязательных переменных окружения
if not BOT_TOKEN:
    logger.error("Не найден BOT_TOKEN в переменных окружения")
    sys.exit(1)

if not WEBHOOK_HOST:
    logger.error("Не найден WEBHOOK_HOST в переменных окружения")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация маршрутизаторов
dp.include_router(registration.router)
dp.include_router(menu.router)
dp.include_router(learning.router)
dp.include_router(training.router)
dp.include_router(settings.router)
dp.include_router(admin.router)
dp.include_router(review.router)

# Инициализация сервиса уведомлений
notification_service = NotificationService(bot)

# Создание middleware для инъекции сессии базы данных
db_session_middleware = DatabaseSessionMiddleware(get_async_session)
dp.message.middleware(db_session_middleware)
dp.callback_query.middleware(db_session_middleware)

# Функция для настройки вебхука
async def on_startup(app):
    """Настройка вебхука при запуске приложения"""
    await bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Вебхук установлен на URL: {WEBHOOK_URL}")

# Функция для очистки при завершении
async def on_shutdown(app):
    """Очистка ресурсов при завершении"""
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Бот остановлен, вебхук удален")

# Маршрут для проверки работоспособности
async def health_check(request):
    """Эндпоинт для проверки работоспособности"""
    return web.Response(text="Bot is running!")

# Создание веб-приложения
app = web.Application()

# Добавление обработчиков событий
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Добавление маршрута для проверки работоспособности
app.router.add_get("/", health_check)

# Настройка обработчика webhook запросов
webhook_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)

# Настройка вебхука в приложении
webhook_handler.register(app, path=WEBHOOK_PATH)

# Настройка aiohttp-приложения
setup_application(app, dp)

# Запуск веб-сервера
if __name__ == "__main__":
    # Получаем порт из переменной окружения или используем 8080 по умолчанию
    PORT = int(os.getenv("PORT", 8080))
    
    logger.info(f"Запуск веб-сервера на порту {PORT}...")
    web.run_app(app, host="0.0.0.0", port=PORT)
