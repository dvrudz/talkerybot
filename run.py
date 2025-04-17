import asyncio
import os
import subprocess
import sys
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

async def run_alembic():
    """Запуск Alembic для создания таблиц в базе данных"""
    logger.info("Запуск миграций Alembic...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Таблицы в базе данных успешно созданы!")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске миграций: {e}")
        return False

async def import_sample_data():
    """Импорт примеров слов в базу данных"""
    logger.info("Импорт примеров слов...")
    try:
        from sample_data import insert_words
        await insert_words()
        logger.info("Примеры слов успешно импортированы!")
        return True
    except Exception as e:
        logger.error(f"Ошибка при импорте примеров слов: {e}")
        return False

async def start_bot():
    """Запуск бота"""
    logger.info("Запуск Telegram-бота...")
    try:
        import bot
        # bot.py содержит бесконечный цикл, поэтому этот код не выполнится до остановки бота
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

async def main():
    # Проверка наличия необходимых переменных окружения
    if not os.getenv("BOT_TOKEN"):
        logger.error("Ошибка: BOT_TOKEN не указан в переменных окружения")
        sys.exit(1)
    
    if not os.getenv("DATABASE_URL"):
        logger.error("Ошибка: DATABASE_URL не указан в переменных окружения")
        sys.exit(1)
    
    # Запуск миграций Alembic
    db_initialized = await run_alembic()
    
    # Импорт примеров данных
    if db_initialized:
        await import_sample_data()
    
    # Запуск бота
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
