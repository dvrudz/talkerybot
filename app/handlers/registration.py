from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.keyboards import language_keyboard, level_keyboard, main_menu_keyboard
from app.services.user_service import UserService
from app.database.db import get_session

router = Router()

class RegistrationForm(StatesGroup):
    name = State()
    language = State()
    level = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Handler for the /start command. Checks if the user exists, if not, starts registration.
    """
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        # User already exists
        await message.answer(
            f"Welcome back, {user.name}! 👋\nLet's continue learning {user.language}!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Start registration
    await message.answer(
        "Welcome to TalkeryBot - your language learning assistant! 🎓\n\n"
        "Let's set up your profile. What's your name?"
    )
    await state.set_state(RegistrationForm.name)

@router.message(RegistrationForm.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Handler for the name input during registration.
    """
    await state.update_data(name=message.text)
    
    await message.answer(
        f"Nice to meet you, {message.text}!\n\n"
        "Which language would you like to learn?",
        reply_markup=language_keyboard()
    )
    await state.set_state(RegistrationForm.language)

@router.message(RegistrationForm.language, F.text.in_(["🇬🇧 English", "🇩🇪 German"]))
async def process_language(message: types.Message, state: FSMContext):
    """
    Handler for the language selection during registration.
    """
    language = "english" if message.text == "🇬🇧 English" else "german"
    await state.update_data(language=language)
    
    await message.answer(
        f"Great! You've chosen to learn {language}.\n\n"
        "Now, please select your current level:",
        reply_markup=level_keyboard()
    )
    await state.set_state(RegistrationForm.level)

@router.message(RegistrationForm.language)
async def process_language_invalid(message: types.Message):
    """
    Handler for invalid language selection.
    """
    await message.answer(
        "Please select a language using the buttons below.",
        reply_markup=language_keyboard()
    )

@router.message(RegistrationForm.level, F.text.in_(["A1", "A2", "B1", "B2"]))
async def process_level(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Handler for the level selection during registration.
    """
    user_data = await state.get_data()
    name = user_data["name"]
    language = user_data["language"]
    level = message.text
    
    # Create user in database
    user_service = UserService(session)
    await user_service.create_user(
        telegram_id=message.from_user.id,
        name=name,
        language=language,
        level=level
    )
    
    await message.answer(
        f"Perfect! Your profile has been created.\n\n"
        f"• Name: {name}\n"
        f"• Language: {language}\n"
        f"• Level: {level}\n\n"
        f"You're all set! Let's start learning 🚀",
        reply_markup=main_menu_keyboard()
    )
    
    # Clear state
    await state.clear()

@router.message(RegistrationForm.level)
async def process_level_invalid(message: types.Message):
    """
    Handler for invalid level selection.
    """
    await message.answer(
        "Please select your level using the buttons below.",
        reply_markup=level_keyboard()
    ) 