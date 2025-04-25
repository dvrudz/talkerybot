#!/usr/bin/env python
import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

def setup_webhook():
    """Настройка вебхука для Telegram бота."""
    bot_token = os.getenv("BOT_TOKEN")
    webhook_host = os.getenv("WEBHOOK_HOST")
    
    if not bot_token:
        logger.error("Ошибка: BOT_TOKEN не задан в переменных окружения.")
        sys.exit(1)
    
    if not webhook_host:
        logger.error("Ошибка: WEBHOOK_HOST не задан в переменных окружения.")
        sys.exit(1)
    
    # Формирование URL для вебхука
    webhook_url = f"{webhook_host}/webhook/{bot_token}"
    
    # Отправка запроса на установку вебхука
    set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}"
    
    try:
        response = requests.get(set_webhook_url)
        response_json = response.json()
        
        if response_json.get("ok"):
            logger.info(f"Вебхук успешно установлен на URL: {webhook_url}")
        else:
            logger.error(f"Ошибка при установке вебхука: {response_json}")
    except Exception as e:
        logger.error(f"Произошла ошибка при запросе к Telegram API: {e}")
        sys.exit(1)

def get_webhook_info():
    """Получение информации о текущем вебхуке."""
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("Ошибка: BOT_TOKEN не задан в переменных окружения.")
        sys.exit(1)
    
    # Отправка запроса на получение информации о вебхуке
    get_webhook_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(get_webhook_url)
        response_json = response.json()
        
        if response_json.get("ok"):
            webhook_info = response_json.get("result", {})
            logger.info(f"Текущая информация о вебхуке:")
            logger.info(f"URL: {webhook_info.get('url', 'Не установлен')}")
            logger.info(f"Использует самоподписанный сертификат: {webhook_info.get('has_custom_certificate', False)}")
            logger.info(f"Ожидающие обновления: {webhook_info.get('pending_update_count', 0)}")
            
            if webhook_info.get("last_error_date"):
                logger.warning(f"Последняя ошибка: {webhook_info.get('last_error_message', 'Нет описания')}")
        else:
            logger.error(f"Ошибка при получении информации о вебхуке: {response_json}")
    except Exception as e:
        logger.error(f"Произошла ошибка при запросе к Telegram API: {e}")
        sys.exit(1)

def delete_webhook():
    """Удаление вебхука."""
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("Ошибка: BOT_TOKEN не задан в переменных окружения.")
        sys.exit(1)
    
    # Отправка запроса на удаление вебхука
    delete_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    try:
        response = requests.get(delete_webhook_url)
        response_json = response.json()
        
        if response_json.get("ok"):
            logger.info("Вебхук успешно удален")
        else:
            logger.error(f"Ошибка при удалении вебхука: {response_json}")
    except Exception as e:
        logger.error(f"Произошла ошибка при запросе к Telegram API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Настройка вебхука для Telegram бота")
    parser.add_argument("action", choices=["setup", "info", "delete"], 
                      help="Действие: setup - установить вебхук, info - получить информацию, delete - удалить вебхук")
    
    args = parser.parse_args()
    
    if args.action == "setup":
        setup_webhook()
    elif args.action == "info":
        get_webhook_info()
    elif args.action == "delete":
        delete_webhook()
