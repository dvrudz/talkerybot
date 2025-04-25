import os
import asyncio
import logging
from aiogram import Bot
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")  # URL вашего приложения на Render.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

async def setup_webhook():
    """Настраивает webhook для бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в переменных окружения")
        return
    
    if not WEBHOOK_HOST:
        logger.error("WEBHOOK_HOST не найден в переменных окружения")
        return
    
    try:
        bot = Bot(token=BOT_TOKEN)
        webhook_info = await bot.get_webhook_info()
        
        # Удаляем текущий webhook, если он установлен
        if webhook_info.url:
            logger.info(f"Удаление текущего webhook: {webhook_info.url}")
            await bot.delete_webhook()
        
        # Устанавливаем новый webhook
        logger.info(f"Установка нового webhook: {WEBHOOK_URL}")
        await bot.set_webhook(url=WEBHOOK_URL)
        
        # Проверяем установку webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Webhook успешно установлен: {webhook_info.url}")
        
        # Получение информации о боте
        bot_info = await bot.get_me()
        logger.info(f"Бот: @{bot_info.username} ({bot_info.id})")
        
        await bot.session.close()
    except Exception as e:
        logger.error(f"Ошибка при настройке webhook: {e}")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
