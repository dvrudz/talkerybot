import asyncio
import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_alembic():
    """Run Alembic to create database tables"""
    print("Running Alembic migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Database tables created successfully!")

async def run_import_data():
    """Import sample data into the database"""
    print("Importing sample data...")
    import sample_data
    await sample_data.insert_words()
    print("Sample data imported successfully!")

async def main():
    # Check if environment variables are set
    if not os.getenv("BOT_TOKEN"):
        print("Error: BOT_TOKEN not set in .env file")
        print("Please create a .env file based on .env.example and set your Telegram bot token")
        sys.exit(1)
    
    if not os.getenv("DATABASE_URL"):
        print("Error: DATABASE_URL not set in .env file")
        print("Please create a .env file based on .env.example and set your database URL")
        sys.exit(1)
    
    # Run Alembic migrations
    run_alembic()
    
    # Import sample data
    await run_import_data()
    
    print("\nInitialization complete! Now you can start the bot with: python bot.py")

if __name__ == "__main__":
    asyncio.run(main()) 