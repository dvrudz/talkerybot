import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

# Set up logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Load environment variables
load_dotenv()

# Import handlers after loading environment variables to avoid circular imports
from app.handlers import registration, menu, learning, training, settings, admin, review
from app.database.db import get_session
from app.services.notification_service import NotificationService

# Initialize bot and dispatcher
bot = Bot(token=os.getenv("BOT_TOKEN"), parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Register all routers
dp.include_router(registration.router)
dp.include_router(menu.router)
dp.include_router(learning.router)
dp.include_router(training.router)
dp.include_router(settings.router)
dp.include_router(admin.router)
dp.include_router(review.router)

# Middleware to inject session into handlers
@dp.update.outer_middleware()
async def db_session_middleware(handler, event, data):
    async for session in get_session():
        data["session"] = session
        return await handler(event, data)

# Function to send notifications
async def send_notifications():
    while True:
        try:
            # Create a new session for the notification service
            async for session in get_session():
                notification_service = NotificationService(session, bot)
                await notification_service.send_review_notifications()
                break  # Exit the session loop after processing
            
            # Wait for the next scheduled time (e.g., every day at 10 AM)
            now = datetime.now()
            next_run = now.replace(hour=10, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run = next_run + timedelta(days=1)
            
            seconds_until_next_run = (next_run - now).total_seconds()
            await asyncio.sleep(seconds_until_next_run)
            
        except Exception as e:
            logging.error(f"Error in notification task: {e}")
            await asyncio.sleep(3600)  # Wait an hour before retrying on error

async def main():
    # Start the notification task
    asyncio.create_task(send_notifications())
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.info("Starting TalkeryBot...")
    asyncio.run(main()) 