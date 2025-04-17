from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.database.models import User, Settings

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalars().first()
    
    async def create_user(self, telegram_id: int, name: str, language: str, level: str) -> User:
        user = User(
            telegram_id=telegram_id,
            name=name,
            language=language,
            level=level
        )
        self.session.add(user)
        await self.session.commit()
        
        # Create default settings for the user
        settings = Settings(
            user_id=user.id,
            notify=True,
            words_per_day=5,
            language=language
        )
        self.session.add(settings)
        await self.session.commit()
        
        return user
    
    async def update_user_language(self, user_id: int, language: str) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(language=language)
        )
        await self.session.execute(
            update(Settings).where(Settings.user_id == user_id).values(language=language)
        )
        await self.session.commit()
    
    async def update_user_level(self, user_id: int, level: str) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(level=level)
        )
        await self.session.commit()
    
    async def get_user_settings(self, user_id: int) -> Settings:
        result = await self.session.execute(
            select(Settings).where(Settings.user_id == user_id)
        )
        return result.scalars().first()
    
    async def update_settings(self, user_id: int, notify: bool = None, words_per_day: int = None) -> None:
        values = {}
        if notify is not None:
            values["notify"] = notify
        if words_per_day is not None:
            values["words_per_day"] = words_per_day
        
        if values:
            await self.session.execute(
                update(Settings).where(Settings.user_id == user_id).values(**values)
            )
            await self.session.commit() 