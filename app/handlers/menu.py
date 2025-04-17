from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.keyboards import (
    main_menu_keyboard, 
    training_options_keyboard,
    settings_keyboard
)
from app.services.user_service import UserService
from app.services.stats_service import StatsService
from app.utils.helpers import format_user_stats

router = Router()

@router.message(F.text == "🔙 Back to Menu")
async def back_to_menu(message: types.Message, state: FSMContext):
    """
    Handler for returning to the main menu.
    """
    await state.clear()
    await message.answer(
        "Main Menu:", 
        reply_markup=main_menu_keyboard()
    )

@router.message(F.text == "📚 Learn New Words")
async def learn_new_words(message: types.Message, state: FSMContext):
    """
    Handler for starting the learn new words mode.
    """
    # The actual learning logic is in the learning.py handler
    # This just informs that we're starting the mode
    await message.answer(
        "Let's learn some new words! I'll show you flashcards with words, translations, and examples.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Let the learning handler take over
    from app.handlers.learning import get_new_word
    await get_new_word(message, state)

@router.message(F.text == "🔄 Training")
async def start_training(message: types.Message, state: FSMContext):
    """
    Handler for starting training mode.
    """
    await message.answer(
        "Training helps reinforce your vocabulary. Choose a training mode:",
        reply_markup=training_options_keyboard()
    )

@router.message(F.text == "📋 My Words")
async def my_words(message: types.Message, state: FSMContext):
    """
    Handler for viewing saved words.
    """
    # The actual words list is in the learning.py handler
    # This just informs that we're starting the mode
    await message.answer(
        "Here are the words you've saved for learning:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Let the learning handler take over
    from app.handlers.learning import get_user_words
    await get_user_words(message, state)

@router.message(F.text == "📊 My Progress")
async def show_progress(message: types.Message, session: AsyncSession):
    """
    Handler for showing user progress and statistics.
    """
    stats_service = StatsService(session)
    user_stats = await stats_service.get_user_stats(message.from_user.id)
    
    formatted_stats = format_user_stats(user_stats)
    
    await message.answer(
        formatted_stats,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )

@router.message(F.text == "⚙️ Settings")
async def show_settings(message: types.Message):
    """
    Handler for showing settings menu.
    """
    await message.answer(
        "Settings:\n\n"
        "Here you can customize your learning experience.",
        reply_markup=settings_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Handler for the /help command.
    """
    help_text = (
        "📚 <b>TalkeryBot Help</b>\n\n"
        "Here's what you can do with this bot:\n\n"
        "• <b>Learn New Words</b> - Study new vocabulary with flashcards\n"
        "• <b>Training</b> - Test your knowledge with exercises\n"
        "• <b>My Words</b> - Review words you're learning\n"
        "• <b>My Progress</b> - See your learning statistics\n"
        "• <b>Settings</b> - Customize your learning experience\n\n"
        "Commands:\n"
        "/start - Start or restart the bot\n"
        "/help - Show this help message\n\n"
        "If you have any issues, please contact @your_support_username"
    )
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    ) 