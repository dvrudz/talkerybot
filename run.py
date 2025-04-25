import asyncio
import os
import subprocess
import sys
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Определяем порт из переменных окружения или используем порт по умолчанию
PORT = int(os.environ.get("PORT", 10000))

# Простой веб-сервер для Render.com
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'TalkeryBot is running!')
    
    def log_message(self, format, *args):
        # Отключаем логирование HTTP-запросов
        return

def create_tables_manually():
    """Создает таблицы напрямую через SQL (если alembic не работает)"""
    logger.info("Создание таблиц вручную...")
    try:
        import asyncio
        import asyncpg
        from app.database.models import Base
        
        async def create_db():
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL не найден в переменных окружения")
                return False
                
            # Убираем asyncpg префикс, если он есть
            if db_url.startswith("postgresql+asyncpg://"):
                conn_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
            else:
                conn_url = db_url
                
            try:
                conn = await asyncpg.connect(conn_url)
                
                # Создаем таблицы
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    language VARCHAR(50) NOT NULL,
                    level VARCHAR(10) NOT NULL,
                    date_joined TIMESTAMP DEFAULT NOW()
                )
                ''')
                
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    notify BOOLEAN DEFAULT TRUE,
                    words_per_day INTEGER DEFAULT 5,
                    language VARCHAR(50)
                )
                ''')
                
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id SERIAL PRIMARY KEY,
                    word VARCHAR(255) NOT NULL,
                    translation VARCHAR(255) NOT NULL,
                    example TEXT,
                    level VARCHAR(10) NOT NULL,
                    language VARCHAR(50) NOT NULL,
                    audio_url VARCHAR(255)
                )
                ''')
                
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_words (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    word_id INTEGER REFERENCES words(id) ON DELETE CASCADE,
                    added_date TIMESTAMP DEFAULT NOW(),
                    next_review TIMESTAMP,
                    review_count INTEGER DEFAULT 0,
                    correct_count INTEGER DEFAULT 0
                )
                ''')
                
                await conn.close()
                logger.info("Таблицы успешно созданы!")
                return True
            except Exception as e:
                logger.error(f"Ошибка при создании таблиц: {e}")
                return False
        
        result = asyncio.run(create_db())
        return result
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц вручную: {e}")
        return False

async def run_alembic():
    """Запуск Alembic для создания таблиц в базе данных"""
    logger.info("Запуск миграций Alembic...")
    try:
        process = subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Таблицы в базе данных успешно созданы!")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске миграций: {e}")
        # Пробуем создать таблицы вручную, если alembic не справился
        return create_tables_manually()

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

def run_web_server():
    """Запуск веб-сервера"""
    server = HTTPServer(('0.0.0.0', PORT), SimpleHTTPRequestHandler)
    logger.info(f"Запуск веб-сервера на порту {PORT}...")
    server.serve_forever()

def start_bot_thread():
    """Запуск бота в отдельном потоке"""
    logger.info("Запуск Telegram-бота...")
    try:
        # Даем время для настройки базы данных
        time.sleep(5)
        import bot
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

async def check_bot_health():
    """Проверяет, что бот запущен и доступен"""
    try:
        # Даем боту время на запуск
        await asyncio.sleep(10)
        
        from aiogram import Bot
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            return
        
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        logger.info(f"Бот успешно запущен: @{bot_info.username} ({bot_info.id})")
        await bot.session.close()
    except Exception as e:
        logger.error(f"Ошибка при проверке бота: {e}")

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
    
    # Запускаем задачу проверки бота
    asyncio.create_task(check_bot_health())
    
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_thread)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запуск веб-сервера в основном потоке
    run_web_server()

if __name__ == "__main__":
    asyncio.run(main())
