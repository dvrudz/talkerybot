from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.keyboards import word_card_keyboard, my_words_keyboard, main_menu_keyboard
from app.services.user_service import UserService
from app.services.word_service import WordService
from app.utils.helpers import format_word_card

router = Router()

class LearningState(StatesGroup):
    viewing_new_word = State()
    viewing_user_word = State()

# ---- New Words Mode ----

async def get_new_word(message: types.Message, state: FSMContext, session: AsyncSession = None):
    """
    Get and display a new random word to the user.
    """
    if not session:
        # For when this function is called from other handlers
        return
    
    # Get user information
    user_service = UserService(session)
    word_service = WordService(session)
    
    user = await user_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(
            "Please start the bot with /start to set up your profile first.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Get a random word
    word = await word_service.get_random_word(user.language, user.level)
    if not word:
        await message.answer(
            "No words available for your current level. Please try again later or change your level in settings.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Store the current word in state
    await state.update_data(current_word_id=word.id)
    await state.set_state(LearningState.viewing_new_word)
    
    # Display the word card
    card_text = format_word_card(
        word=word.word,
        translation=word.translation,
        example=word.example,
        audio_url=word.audio_url
    )
    
    await message.answer(
        card_text,
        parse_mode="HTML",
        reply_markup=word_card_keyboard()
    )

@router.callback_query(LearningState.viewing_new_word, F.data == "next_word")
async def next_word(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Show next random word.
    """
    await callback.answer()
    
    # Get a new random word
    await get_new_word(callback.message, state, session)

@router.callback_query(LearningState.viewing_new_word, F.data == "add_word")
async def add_word_to_user(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Add the current word to user's learning list.
    """
    data = await state.get_data()
    current_word_id = data.get("current_word_id")
    
    if not current_word_id:
        await callback.answer("Word not found.")
        return
    
    # Get user info
    user_service = UserService(session)
    word_service = WordService(session)
    
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    
    # Add word to user's list
    await word_service.add_word_to_user(user.id, current_word_id)
    
    await callback.answer("Word added to your learning list!")
    
    # Show next word
    await get_new_word(callback.message, state, session)

@router.callback_query(LearningState.viewing_new_word, F.data == "back_to_menu")
async def back_to_menu_from_learning(callback: types.CallbackQuery, state: FSMContext):
    """
    Return to main menu from learning mode.
    """
    await callback.answer()
    await state.clear()
    
    await callback.message.answer(
        "Returning to main menu.",
        reply_markup=main_menu_keyboard()
    )
    
# ---- My Words Mode ----

async def get_user_words(message: types.Message, state: FSMContext, session: AsyncSession = None):
    """
    Show the user's saved words.
    """
    if not session:
        # For when this function is called from other handlers
        return
    
    # Get user information
    user_service = UserService(session)
    word_service = WordService(session)
    
    user = await user_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(
            "Please start the bot with /start to set up your profile first.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Get user's words
    user_words = await word_service.get_user_words(user.id)
    if not user_words:
        await message.answer(
            "You haven't added any words to your learning list yet. "
            "Go to 'Learn New Words' to add some!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Get the first word
    user_word, word = user_words[0]
    
    # Store data in state
    await state.update_data(
        user_words_ids=[uw.id for uw, _ in user_words],
        word_ids=[w.id for _, w in user_words],
        current_index=0
    )
    await state.set_state(LearningState.viewing_user_word)
    
    # Display the word card
    card_text = format_word_card(
        word=word.word,
        translation=word.translation,
        example=word.example,
        audio_url=word.audio_url
    )
    
    # Add review information
    card_text += f"\n\n📊 <b>Stats:</b>\n"
    card_text += f"• Reviews: {user_word.review_count}\n"
    card_text += f"• Correct answers: {user_word.correct_count}\n"
    
    await message.answer(
        card_text,
        parse_mode="HTML",
        reply_markup=my_words_keyboard()
    )

@router.callback_query(LearningState.viewing_user_word, F.data == "next_my_word")
async def next_my_word(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Show next word from user's list.
    """
    await callback.answer()
    
    # Get data from state
    data = await state.get_data()
    user_words_ids = data.get("user_words_ids", [])
    word_ids = data.get("word_ids", [])
    current_index = data.get("current_index", 0)
    
    # Move to next word
    next_index = (current_index + 1) % len(user_words_ids) if user_words_ids else 0
    
    # Update state
    await state.update_data(current_index=next_index)
    
    # Get the word data
    word_service = WordService(session)
    user_word = await session.get("UserWord", user_words_ids[next_index])
    word = await session.get("Word", word_ids[next_index])
    
    # Display the word card
    card_text = format_word_card(
        word=word.word,
        translation=word.translation,
        example=word.example,
        audio_url=word.audio_url
    )
    
    # Add review information
    card_text += f"\n\n📊 <b>Stats:</b>\n"
    card_text += f"• Reviews: {user_word.review_count}\n"
    card_text += f"• Correct answers: {user_word.correct_count}\n"
    
    await callback.message.edit_text(
        card_text,
        parse_mode="HTML",
        reply_markup=my_words_keyboard()
    )

@router.callback_query(LearningState.viewing_user_word, F.data == "remove_word")
async def remove_my_word(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Remove current word from user's learning list.
    """
    # Get data from state
    data = await state.get_data()
    user_words_ids = data.get("user_words_ids", [])
    word_ids = data.get("word_ids", [])
    current_index = data.get("current_index", 0)
    
    if not user_words_ids or current_index >= len(user_words_ids):
        await callback.answer("Word not found.")
        return
    
    # Get user and word IDs
    user_service = UserService(session)
    word_service = WordService(session)
    
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    word_id = word_ids[current_index]
    
    # Remove word
    await word_service.remove_word_from_user(user.id, word_id)
    
    # Remove from lists
    user_words_ids.pop(current_index)
    word_ids.pop(current_index)
    
    # If no words left
    if not user_words_ids:
        await callback.answer("Word removed. No more words in your list.")
        await state.clear()
        
        await callback.message.edit_text(
            "You've removed all words from your learning list. "
            "Go to 'Learn New Words' to add some more!",
            reply_markup=None
        )
        
        await callback.message.answer(
            "Returning to main menu.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Update index if needed
    if current_index >= len(user_words_ids):
        current_index = 0
    
    # Update state
    await state.update_data(
        user_words_ids=user_words_ids,
        word_ids=word_ids,
        current_index=current_index
    )
    
    await callback.answer("Word removed from your learning list.")
    
    # Show next word
    user_word = await session.get("UserWord", user_words_ids[current_index])
    word = await session.get("Word", word_ids[current_index])
    
    # Display the word card
    card_text = format_word_card(
        word=word.word,
        translation=word.translation,
        example=word.example,
        audio_url=word.audio_url
    )
    
    # Add review information
    card_text += f"\n\n📊 <b>Stats:</b>\n"
    card_text += f"• Reviews: {user_word.review_count}\n"
    card_text += f"• Correct answers: {user_word.correct_count}\n"
    
    await callback.message.edit_text(
        card_text,
        parse_mode="HTML",
        reply_markup=my_words_keyboard()
    )

@router.callback_query(LearningState.viewing_user_word, F.data == "back_to_menu")
async def back_to_menu_from_my_words(callback: types.CallbackQuery, state: FSMContext):
    """
    Return to main menu from my words mode.
    """
    await callback.answer()
    await state.clear()
    
    await callback.message.answer(
        "Returning to main menu.",
        reply_markup=main_menu_keyboard()
    ) 