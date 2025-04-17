from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.database.models import User, UserWord, Word, Settings
from app.keyboards.keyboards import review_now_keyboard

class NotificationService:
    def __init__(self, session: AsyncSession, bot):
        self.session = session
        self.bot = bot
    
    async def send_review_notifications(self):
        """
        Send notifications to users who have words due for review.
        """
        now = datetime.utcnow()
        
        # Get users with notifications enabled and words to review
        result = await self.session.execute(
            select(User, Settings, UserWord, Word)
            .join(Settings, User.id == Settings.user_id)
            .join(UserWord, User.id == UserWord.user_id)
            .join(Word, UserWord.word_id == Word.id)
            .where(
                and_(
                    Settings.notify == True,
                    UserWord.next_review <= now
                )
            )
            .group_by(User.id, Settings.user_id, UserWord.id, Word.id)
        )
        
        # Group by user
        users_to_notify = {}
        for user, settings, user_word, word in result:
            if user.telegram_id not in users_to_notify:
                users_to_notify[user.telegram_id] = {
                    'user': user,
                    'settings': settings,
                    'words': []
                }
            
            users_to_notify[user.telegram_id]['words'].append((user_word, word))
        
        # Send notifications
        for telegram_id, data in users_to_notify.items():
            user = data['user']
            words = data['words']
            
            if not words:
                continue
            
            # Format notification message
            words_count = len(words)
            sample_words = [word.word for _, word in words[:3]]
            
            message = (
                f"🔔 <b>Time for a review!</b>\n\n"
                f"You have {words_count} word{'s' if words_count > 1 else ''} "
                f"to review today, including:\n"
                f"• {', '.join(sample_words)}"
                f"{' and more...' if words_count > 3 else ''}\n\n"
                f"Regular review is key to effective learning! 🧠"
            )
            
            # Send notification
            try:
                await self.bot.send_message(
                    telegram_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=review_now_keyboard()
                )
            except Exception as e:
                print(f"Failed to send notification to user {telegram_id}: {e}")
    
    async def get_words_due_for_review(self, user_id: int):
        """
        Get words that are due for review for a specific user.
        """
        now = datetime.utcnow()
        
        result = await self.session.execute(
            select(UserWord, Word)
            .join(Word, UserWord.word_id == Word.id)
            .where(
                and_(
                    UserWord.user_id == user_id,
                    UserWord.next_review <= now
                )
            )
        )
        
        return result.all() 