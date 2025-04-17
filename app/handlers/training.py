from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
import random

from app.keyboards.keyboards import main_menu_keyboard, quiz_answer_keyboard
from app.services.user_service import UserService
from app.services.word_service import WordService
from app.utils.helpers import generate_options, generate_fill_in_blank

router = Router()

class TrainingState(StatesGroup):
    quiz = State()
    fill_in_blank = State()

@router.message(F.text == "🔤 Translation Quiz")
async def start_translation_quiz(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Start translation quiz training.
    """
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
    
    # Get user's words or random words if user doesn't have enough
    user_words = await word_service.get_user_words(user.id)
    if user_words and len(user_words) >= 4:
        # Use user's own words for the quiz
        random.shuffle(user_words)
        correct_pair = user_words[0]
        other_words = [word for _, word in user_words[1:]]
        correct_word_obj = correct_pair[1]
        
        # Use the user_word_id for tracking later
        user_word_id = correct_pair[0].id
        source = "user_words"
    else:
        # Not enough user words, use random words
        words = await word_service.get_random_words_for_quiz(user.language, user.level, 4)
        if not words or len(words) < 4:
            await message.answer(
                "Not enough words available for quiz. Please try again later.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        correct_word_obj = words[0]
        other_words = words[1:]
        user_word_id = None
        source = "random"
    
    # Generate quiz options
    options, correct_index = generate_options(correct_word_obj, other_words)
    
    # Store quiz data in state
    await state.update_data(
        correct_index=correct_index,
        correct_word_id=correct_word_obj.id,
        user_word_id=user_word_id,
        source=source
    )
    await state.set_state(TrainingState.quiz)
    
    # Display the quiz
    await message.answer(
        f"Translate the word:\n\n<b>{correct_word_obj.word}</b>",
        parse_mode="HTML",
        reply_markup=quiz_answer_keyboard(options)
    )

@router.callback_query(TrainingState.quiz, F.data.startswith("answer_"))
async def process_quiz_answer(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Process the user's answer to a quiz question.
    """
    # Get the selected answer index
    selected_index = int(callback.data.split("_")[1])
    
    # Get saved data
    data = await state.get_data()
    correct_index = data.get("correct_index")
    correct_word_id = data.get("correct_word_id")
    user_word_id = data.get("user_word_id")
    source = data.get("source")
    
    # Check the answer
    is_correct = selected_index == correct_index
    
    # Get the correct word for feedback
    word = await session.get("Word", correct_word_id)
    
    # Update stats if the word is from user's list
    if user_word_id and source == "user_words":
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
    
    # Ask if they want to continue
    await callback.message.answer(
        "Would you like another question?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Yes", callback_data="quiz_continue"),
                types.InlineKeyboardButton(text="❌ No, back to menu", callback_data="back_to_menu")
            ]
        ])
    )

@router.callback_query(F.data == "quiz_continue")
async def continue_quiz(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Continue with another quiz question.
    """
    await callback.answer()
    
    # Start a new quiz question
    await start_translation_quiz(callback.message, state, session)

@router.message(F.text == "📝 Fill in the Blank")
async def start_fill_in_blank(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Start fill in the blank training.
    """
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
    
    # Get user's words or random words if user doesn't have enough
    user_words = await word_service.get_user_words(user.id)
    if user_words:
        # Use user's own words
        random.shuffle(user_words)
        correct_pair = user_words[0]
        correct_word_obj = correct_pair[1]
        
        # Use the user_word_id for tracking later
        user_word_id = correct_pair[0].id
        source = "user_words"
    else:
        # No user words, use random word
        word = await word_service.get_random_word(user.language, user.level)
        if not word:
            await message.answer(
                "No words available for exercises. Please try again later.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        correct_word_obj = word
        user_word_id = None
        source = "random"
    
    # Generate exercise
    exercise, answer = generate_fill_in_blank(correct_word_obj.example, correct_word_obj.word)
    
    # Store exercise data in state
    await state.update_data(
        answer=answer,
        correct_word_id=correct_word_obj.id,
        user_word_id=user_word_id,
        source=source
    )
    await state.set_state(TrainingState.fill_in_blank)
    
    # Display the exercise
    await message.answer(
        f"Fill in the blank or translate:\n\n<b>{exercise}</b>\n\nType your answer:",
        parse_mode="HTML"
    )

@router.message(TrainingState.fill_in_blank)
async def process_fill_in_blank(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Process the user's answer to a fill in the blank exercise.
    """
    user_answer = message.text.strip().lower()
    
    # Get saved data
    data = await state.get_data()
    correct_answer = data.get("answer", "").lower()
    correct_word_id = data.get("correct_word_id")
    user_word_id = data.get("user_word_id")
    source = data.get("source")
    
    # Check the answer - allow for some flexibility
    is_correct = (
        user_answer == correct_answer or
        user_answer in correct_answer or
        correct_answer in user_answer
    )
    
    # Get the correct word for feedback
    word = await session.get("Word", correct_word_id)
    
    # Update stats if the word is from user's list
    if user_word_id and source == "user_words":
        word_service = WordService(session)
        await word_service.update_review_status(user_word_id, is_correct)
    
    # Prepare feedback message
    if is_correct:
        feedback = f"✅ Correct! The answer is <b>{correct_answer}</b>."
    else:
        feedback = f"❌ Incorrect. The correct answer is <b>{correct_answer}</b>."
    
    if word.example:
        feedback += f"\n\nExample: <i>{word.example}</i>"
    
    # Show feedback
    await message.answer(
        feedback,
        parse_mode="HTML"
    )
    
    # Ask if they want to continue
    await message.answer(
        "Would you like another exercise?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Yes", callback_data="fill_continue"),
                types.InlineKeyboardButton(text="❌ No, back to menu", callback_data="back_to_menu")
            ]
        ])
    )

@router.callback_query(F.data == "fill_continue")
async def continue_fill(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Continue with another fill in the blank exercise.
    """
    await callback.answer()
    
    # Start a new exercise
    await start_fill_in_blank(callback.message, state, session)

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """
    Return to main menu from training.
    """
    await callback.answer()
    await state.clear()
    
    await callback.message.answer(
        "Returning to main menu.",
        reply_markup=main_menu_keyboard()
    ) 