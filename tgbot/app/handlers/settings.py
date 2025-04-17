from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.keyboards import (
    language_keyboard, level_keyboard, 
    main_menu_keyboard, words_per_day_keyboard,
    yes_no_keyboard
)
from app.services.user_service import UserService
from app.services.word_service import WordService

router = Router()

class SettingsState(StatesGroup):
    language_change = State()
    level_change = State()
    words_per_day = State()
    notifications = State()
    reset_confirm = State()

@router.message(F.text == "🔄 Change Language")
async def change_language(message: types.Message, state: FSMContext):
    """
    Handler for changing the learning language.
    """
    await message.answer(
        "Select the language you want to learn:",
        reply_markup=language_keyboard()
    )
    await state.set_state(SettingsState.language_change)

@router.message(SettingsState.language_change, F.text.in_(["🇬🇧 English", "🇩🇪 German"]))
async def process_language_change(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Process language change selection.
    """
    language = "english" if message.text == "🇬🇧 English" else "german"
    
    # Update user language
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        await user_service.update_user_language(user.id, language)
        
        await message.answer(
            f"Your learning language has been updated to {language}!",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "User not found. Please restart with /start.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()

@router.message(F.text == "📊 Change Words Per Day")
async def change_words_per_day(message: types.Message, state: FSMContext):
    """
    Handler for changing words per day setting.
    """
    await message.answer(
        "How many new words would you like to learn per day?",
        reply_markup=words_per_day_keyboard()
    )
    await state.set_state(SettingsState.words_per_day)

@router.callback_query(SettingsState.words_per_day, F.data.startswith("words_per_day_"))
async def process_words_per_day(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Process words per day selection.
    """
    await callback.answer()
    
    # Extract the selected number
    words_count = int(callback.data.split("_")[-1])
    
    # Update user settings
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    
    if user:
        await user_service.update_settings(user.id, words_per_day=words_count)
        
        await callback.message.edit_text(
            f"Your daily word count has been updated to {words_count} words per day!"
        )
        
        await callback.message.answer(
            "Setting updated!",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
    else:
        await callback.message.edit_text(
            "User not found. Please restart with /start."
        )
        await state.clear()

@router.message(F.text == "🔔 Toggle Notifications")
async def toggle_notifications(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Handler for toggling notifications.
    """
    # Get current notification status
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer(
            "User not found. Please restart with /start.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    settings = await user_service.get_user_settings(user.id)
    current_status = settings.notify
    
    # Store user ID in state
    await state.update_data(user_id=user.id)
    await state.set_state(SettingsState.notifications)
    
    await message.answer(
        f"Notifications are currently {'ON' if current_status else 'OFF'}.\n\n"
        f"Would you like to turn notifications {'OFF' if current_status else 'ON'}?",
        reply_markup=yes_no_keyboard()
    )

@router.callback_query(SettingsState.notifications, F.data.startswith("confirm_"))
async def process_notification_toggle(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Process notification toggle selection.
    """
    await callback.answer()
    
    # Get the answer
    answer = callback.data.split("_")[1]
    
    if answer == "yes":
        # Get user ID from state
        data = await state.get_data()
        user_id = data.get("user_id")
        
        # Get current status
        user_service = UserService(session)
        settings = await user_service.get_user_settings(user_id)
        current_status = settings.notify
        
        # Toggle notification status
        new_status = not current_status
        await user_service.update_settings(user_id, notify=new_status)
        
        await callback.message.edit_text(
            f"Notifications have been turned {'ON' if new_status else 'OFF'}!"
        )
    else:
        await callback.message.edit_text(
            "Notification settings remained unchanged."
        )
    
    await callback.message.answer(
        "Back to main menu",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

@router.message(F.text == "🔄 Reset Progress")
async def reset_progress(message: types.Message, state: FSMContext):
    """
    Handler for resetting user progress.
    """
    await message.answer(
        "⚠️ Warning! This will reset all your learning progress, including:\n"
        "• All saved words\n"
        "• Learning statistics\n"
        "• Review history\n\n"
        "This action cannot be undone. Are you sure?",
        reply_markup=yes_no_keyboard()
    )
    await state.set_state(SettingsState.reset_confirm)

@router.callback_query(SettingsState.reset_confirm, F.data.startswith("confirm_"))
async def process_reset_confirm(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Process reset progress confirmation.
    """
    await callback.answer()
    
    # Get the answer
    answer = callback.data.split("_")[1]
    
    if answer == "yes":
        # Delete all user words
        user_service = UserService(session)
        word_service = WordService(session)
        
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        if user:
            # Delete all UserWord records for this user
            await session.execute(
                f"DELETE FROM user_words WHERE user_id = {user.id}"
            )
            await session.commit()
            
            await callback.message.edit_text(
                "Your progress has been reset. All words and statistics have been cleared."
            )
        else:
            await callback.message.edit_text(
                "User not found. Please restart with /start."
            )
    else:
        await callback.message.edit_text(
            "Reset canceled. Your learning progress is safe."
        )
    
    await callback.message.answer(
        "Back to main menu",
        reply_markup=main_menu_keyboard()
    )
    await state.clear() 