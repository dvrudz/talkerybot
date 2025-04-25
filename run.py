import asyncio
import os
import subprocess
import sys
import logging
import threading
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

def run_web_server():
    """Запуск веб-сервера"""
    server = HTTPServer(('0.0.0.0', PORT), SimpleHTTPRequestHandler)
    logger.info(f"Запуск веб-сервера на порту {PORT}...")
    server.serve_forever()

def start_bot_thread():
    """Запуск бота в отдельном потоке"""
    logger.info("Запуск Telegram-бота...")
    try:
        import bot
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
    
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_thread)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запуск веб-сервера в основном потоке
    run_web_server()

if __name__ == "__main__":
    asyncio.run(main())
