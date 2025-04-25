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

async def reset_webhook():
    """Сбрасывает webhook и переводит бота в режим polling"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в переменных окружения")
        return
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Получаем текущую информацию о webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Текущие настройки webhook: {webhook_info}")
        
        # Если webhook настроен, сбрасываем его
        if webhook_info.url:
            await bot.delete_webhook()
            logger.info("Webhook успешно удален")
        else:
            logger.info("Webhook не был настроен")
        
        # Проверяем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"Бот: @{bot_info.username} ({bot_info.id})")
        
        await bot.session.close()
        logger.info("Теперь бот должен работать в режиме polling")
    except Exception as e:
        logger.error(f"Ошибка при сбросе webhook: {e}")

if __name__ == "__main__":
    asyncio.run(reset_webhook())
