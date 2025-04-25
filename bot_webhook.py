#!/usr/bin/env python
import asyncio
import logging
import os
import sys
from datetime import time, datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from dotenv import load_dotenv

from app.handlers import registration, menu, learning, training, settings, admin, review
from app.middlewares.db_middleware import DbSessionMiddleware
from app.services.db import create_session_pool
from app.services.notification_service import send_review_notifications

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Проверка наличия необходимых переменных окружения
if not BOT_TOKEN:
    logging.error("Пожалуйста, установите переменную окружения BOT_TOKEN")
    sys.exit(1)

if not WEBHOOK_HOST:
    logging.error("Пожалуйста, установите переменную окружения WEBHOOK_HOST")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dispatcher = Dispatcher()

# Регистрация роутеров для разных функциональностей
dispatcher.include_router(registration.router)
dispatcher.include_router(menu.router)
dispatcher.include_router(learning.router)
dispatcher.include_router(training.router)
dispatcher.include_router(settings.router)
dispatcher.include_router(admin.router)
dispatcher.include_router(review.router)

# Функция для отправки уведомлений в определенное время
async def scheduled_notifications():
    notification_time = time(10, 0)  # 10:00 AM
    while True:
        now = datetime.now().time()
        
        # Проверяем, наступило ли время отправки уведомлений
        if now.hour == notification_time.hour and now.minute == notification_time.minute:
            try:
                await send_review_notifications(bot)
                logging.info("Уведомления о повторении отправлены")
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомлений: {e}")
        
        # Ждем 1 минуту перед следующей проверкой
        await asyncio.sleep(60)

async def on_startup(bot: Bot):
    # Настройка вебхука
    await bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Вебхук установлен на {WEBHOOK_URL}")
    
    # Запуск задачи отправки уведомлений
    asyncio.create_task(scheduled_notifications())

async def on_shutdown(bot: Bot):
    # Удаление вебхука при выключении
    await bot.delete_webhook()
    logging.info("Вебхук удален")

async def main():
    # Создание пула сессий базы данных
    session_pool = await create_session_pool()
    
    # Регистрация middleware для добавления сессии базы данных в хэндлеры
    dispatcher.update.middleware(DbSessionMiddleware(session_pool))
    
    # Создание веб-приложения
    app = web.Application()
    
    # Настройка обработчика вебхуков
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настройка запуска и завершения
    setup_application(app, dispatcher, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)
    
    # Запуск веб-сервера
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8080))
    logging.info(f"Запуск webhook сервера на {host}:{port}")
    
    # Запуск веб-приложения
    web.run_app(app, host=host, port=port)

if __name__ == "__main__":
    logging.info("Запуск бота TalkeryBot в режиме webhook")
    asyncio.run(main())
