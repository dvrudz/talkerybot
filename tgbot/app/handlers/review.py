from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
import random

from app.keyboards.keyboards import main_menu_keyboard, quiz_answer_keyboard
from app.services.user_service import UserService
from app.services.word_service import WordService
from app.services.notification_service import NotificationService
from app.utils.helpers import generate_options, format_word_card

router = Router()

class ReviewState(StatesGroup):
    reviewing = State()
    answering = State()

@router.callback_query(F.data == "review_now")
async def start_review(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start reviewing words that are due for review"""
    await callback.answer()
    
    # Get user
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.message.answer(
            "Please start the bot with /start to set up your profile first.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Get words due for review
    notification_service = NotificationService(session, callback.bot)
    review_words = await notification_service.get_words_due_for_review(user.id)
    
    if not review_words:
        await callback.message.answer(
            "You don't have any words to review at the moment.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Prepare for review
    await callback.message.answer(
        f"Let's review {len(review_words)} words that are due today! 🔍\n"
        f"I'll show you the words and ask for translations."
    )
    
    # Store review data in state
    await state.update_data(
        review_words=[(uw.id, w.id) for uw, w in review_words],
        current_index=0
    )
    
    # Show first review
    await show_next_review(callback.message, state, session)

async def show_next_review(message, state: FSMContext, session: AsyncSession):
    """Show the next word for review"""
    # Get data from state
    data = await state.get_data()
    review_words = data.get("review_words", [])
    current_index = data.get("current_index", 0)
    
    # Check if we've reviewed all words
    if current_index >= len(review_words):
        await message.answer(
            "🎉 Congratulations! You've completed all your reviews for today.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return
    
    # Get the current word
    user_word_id, word_id = review_words[current_index]
    word = await session.get("Word", word_id)
    
    # Get some random words for quiz options
    word_service = WordService(session)
    other_words = await word_service.get_random_words_for_quiz(
        word.language, word.level, 3
    )
    
    # Generate quiz options
    options, correct_index = generate_options(word, other_words)
    
    # Store quiz data in state
    await state.update_data(
        current_word_id=word_id,
        current_user_word_id=user_word_id,
        correct_index=correct_index
    )
    await state.set_state(ReviewState.answering)
    
    # Display the quiz
    await message.answer(
        f"Translate the word:\n\n<b>{word.word}</b>",
        parse_mode="HTML",
        reply_markup=quiz_answer_keyboard(options)
    )

@router.callback_query(ReviewState.answering, F.data.startswith("answer_"))
async def process_review_answer(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process the user's answer to a review question"""
    # Get the selected answer index
    selected_index = int(callback.data.split("_")[1])
    
    # Get saved data
    data = await state.get_data()
    correct_index = data.get("correct_index")
    word_id = data.get("current_word_id")
    user_word_id = data.get("current_user_word_id")
    current_index = data.get("current_index", 0)
    
    # Check the answer
    is_correct = selected_index == correct_index
    
    # Get the word for feedback
    word = await session.get("Word", word_id)
    
    # Update stats
    word_service = WordService(session)
    await word_service.update_review_status(user_word_id, is_correct)
    
    # Prepare feedback message
    if is_correct:
        feedback = f"✅ Correct! <b>{word.word}</b> means <b>{word.translation}</b>."
    else:
        feedback = f"❌ Incorrect. <b>{word.word}</b> means <b>{word.translation}</b>."
    
    if word.example:
        feedback += f"\n\nExample: <i>{word.example}</i>"
    
    # Show feedback
    await callback.message.edit_text(
        feedback,
        parse_mode="HTML"
    )
    
    # Move to the next word
    await state.update_data(current_index=current_index + 1)
    
    # Continue with next word
    await callback.message.answer("Moving to the next word...")
    await show_next_review(callback.message, state, session) 