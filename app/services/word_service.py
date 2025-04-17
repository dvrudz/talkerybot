from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from app.database.models import Word, UserWord, User

class WordService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_random_word(self, language: str, level: str) -> Word:
        """Get a random word for the learning mode"""
        result = await self.session.execute(
            select(Word).where(
                Word.language == language,
                Word.level == level
            ).order_by(func.random()).limit(1)
        )
        return result.scalars().first()
    
    async def get_random_words_for_quiz(self, language: str, level: str, count: int = 4) -> list[Word]:
        """Get random words for quiz options"""
        result = await self.session.execute(
            select(Word).where(
                Word.language == language,
                Word.level == level
            ).order_by(func.random()).limit(count)
        )
        return result.scalars().all()
    
    async def add_word_to_user(self, user_id: int, word_id: int) -> UserWord:
        """Add a word to user's learning list"""
        # Check if the word is already added
        result = await self.session.execute(
            select(UserWord).where(
                UserWord.user_id == user_id,
                UserWord.word_id == word_id
            )
        )
        existing = result.scalars().first()
        
        if existing:
            return existing
        
        user_word = UserWord(
            user_id=user_id,
            word_id=word_id,
            next_review=datetime.utcnow() + timedelta(days=1)
        )
        self.session.add(user_word)
        await self.session.commit()
        return user_word
    
    async def remove_word_from_user(self, user_id: int, word_id: int) -> bool:
        """Remove a word from user's learning list"""
        result = await self.session.execute(
            delete(UserWord).where(
                UserWord.user_id == user_id,
                UserWord.word_id == word_id
            )
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_user_words(self, user_id: int) -> list[tuple[UserWord, Word]]:
        """Get all words added by user"""
        result = await self.session.execute(
            select(UserWord, Word).join(Word, UserWord.word_id == Word.id).where(
                UserWord.user_id == user_id
            )
        )
        return result.all()
    
    async def get_words_for_review(self, user_id: int) -> list[tuple[UserWord, Word]]:
        """Get words that need to be reviewed today"""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(UserWord, Word).join(Word, UserWord.word_id == Word.id).where(
                UserWord.user_id == user_id,
                UserWord.next_review <= now
            )
        )
        return result.all()
    
    async def update_review_status(self, user_word_id: int, correct: bool) -> None:
        """Update the review status of a word"""
        user_word = await self.session.get(UserWord, user_word_id)
        if not user_word:
            return
        
        # Update review count and correct count
        user_word.review_count += 1
        if correct:
            user_word.correct_count += 1
        
        # Calculate next review based on spaced repetition algorithm
        days_to_add = self._calculate_next_review_interval(user_word.review_count, correct)
        user_word.next_review = datetime.utcnow() + timedelta(days=days_to_add)
        
        await self.session.commit()
    
    def _calculate_next_review_interval(self, review_count: int, correct: bool) -> int:
        """Calculate days until next review using spaced repetition algorithm"""
        if not correct:
            return 1  # If answered incorrectly, review tomorrow
        
        # Simple spaced repetition formula
        if review_count == 0:
            return 1
        elif review_count == 1:
            return 3
        elif review_count == 2:
            return 7
        elif review_count == 3:
            return 14
        elif review_count == 4:
            return 30
        else:
            return 60  # Max interval is 60 days 