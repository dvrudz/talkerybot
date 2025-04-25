import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from datetime import datetime, time
import pytz

# Добавляем директорию проекта в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт обработчиков
from app.handlers import (
    registration, menu, learning, training, settings, admin, review
)
from app.middleware.db_session import DBSessionMiddleware
from app.services.notification_service import NotificationService
from app.database.session import async_session

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Настройки для webhook
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")  # URL вашего приложения на Render.com
WEBHOOK_PATH = f"/webhook/{os.getenv('BOT_TOKEN')}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"), parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Регистрация роутеров
dp.include_router(registration.router)
dp.include_router(menu.router)
dp.include_router(learning.router)
dp.include_router(training.router)
dp.include_router(settings.router)
dp.include_router(admin.router)
dp.include_router(review.router)

# Добавляем middleware для инъекции сессии БД
dp.update.middleware(DBSessionMiddleware(async_session))

# Планировщик уведомлений
notification_time = time(10, 0)  # 10:00 AM

async def send_notifications():
    """Отправляет уведомления о запланированных повторениях слов"""
    while True:
        try:
            now = datetime.now(pytz.UTC)
            moscow_time = now.astimezone(pytz.timezone('Europe/Moscow'))
            current_time = moscow_time.time()
            
            # Проверяем, наступило ли время отправки уведомлений (10:00)
            if (current_time.hour == notification_time.hour and 
                current_time.minute == notification_time.minute):
                logger.info("Начинаем отправку уведомлений о повторении слов...")
                
                async for session in async_session():
                    notification_service = NotificationService(session)
                    await notification_service.send_review_notifications(bot)
                
                logger.info("Уведомления успешно отправлены.")
                
                # Ждем до следующего дня
                await asyncio.sleep(60 * 60 * 23)  # 23 часа
            else:
                # Проверяем каждую минуту
                await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой

async def on_startup(bot: Bot):
    """Выполняется при запуске бота"""
    # Устанавливаем вебхук
    await bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook установлен на {WEBHOOK_URL}")
    
    # Запускаем задачу отправки уведомлений
    asyncio.create_task(send_notifications())

async def on_shutdown(bot: Bot):
    """Выполняется при остановке бота"""
    await bot.delete_webhook()
    logger.info("Webhook удален")

def main():
    # Создаем приложение aiohttp
    app = web.Application()
    
    # Настраиваем webhook обработчик
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем обработчики запуска и завершения
    setup_application(app, dp, bot=bot, 
                      on_startup=on_startup, 
                      on_shutdown=on_shutdown)
    
    # Запускаем приложение
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
    
    logger.info(f"Server started at {WEBAPP_HOST}:{WEBAPP_PORT}")

if __name__ == "__main__":
    logger.info("Бот запускается...")
    main()
