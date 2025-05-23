import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

load_dotenv()

# Получаем URL базы данных из переменной окружения
original_db_url = os.getenv("DATABASE_URL")

# Модифицируем URL для работы с asyncpg, если начинается с postgresql://
DATABASE_URL = original_db_url
if original_db_url and original_db_url.startswith("postgresql://"):
    DATABASE_URL = original_db_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
