from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.database.models import User, UserWord, Word

class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Get comprehensive statistics for a user"""
        
        # Get total words being learned
        result = await self.session.execute(
            select(func.count()).select_from(UserWord).where(UserWord.user_id == user_id)
        )
        total_words = result.scalar() or 0
        
        # Get words that need review today
        now = datetime.utcnow()
        result = await self.session.execute(
            select(func.count()).select_from(UserWord).where(
                and_(
                    UserWord.user_id == user_id,
                    UserWord.next_review <= now
                )
            )
        )
        words_to_review = result.scalar() or 0
        
        # Get average correctness
        result = await self.session.execute(
            select(
                func.sum(UserWord.correct_count),
                func.sum(UserWord.review_count)
            ).where(UserWord.user_id == user_id)
        )
        correct_sum, review_sum = result.first()
        
        correct_sum = correct_sum or 0
        review_sum = review_sum or 0
        
        if review_sum > 0:
            accuracy = round((correct_sum / review_sum) * 100, 1)
        else:
            accuracy = 0
        
        # Get words learned in the last 7 days
        week_ago = now - timedelta(days=7)
        result = await self.session.execute(
            select(func.count()).select_from(UserWord).where(
                and_(
                    UserWord.user_id == user_id,
                    UserWord.added_date >= week_ago
                )
            )
        )
        words_added_last_week = result.scalar() or 0
        
        # Get most recently studied words
        result = await self.session.execute(
            select(Word.word, Word.translation, UserWord.review_count).
            join(Word, UserWord.word_id == Word.id).
            where(UserWord.user_id == user_id).
            order_by(UserWord.added_date.desc()).
            limit(5)
        )
        recent_words = result.all()
        
        return {
            "total_words": total_words,
            "words_to_review": words_to_review,
            "accuracy": accuracy,
            "words_added_last_week": words_added_last_week,
            "recent_words": recent_words
        }
    
    async def get_all_users_stats(self) -> list[dict]:
        """Get basic stats for all users (admin function)"""
        result = await self.session.execute(
            select(
                User.id, 
                User.name,
                User.language,
                User.level,
                func.count(UserWord.id).label("word_count")
            ).
            outerjoin(UserWord, User.id == UserWord.user_id).
            group_by(User.id).
            order_by(User.date_joined.desc())
        )
        
        users = []
        for user_id, name, language, level, word_count in result.all():
            users.append({
                "user_id": user_id,
                "name": name,
                "language": language,
                "level": level,
                "words_count": word_count
            })
            
        return users 