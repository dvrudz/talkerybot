from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
import csv
import io

from app.database.models import Word
from app.services.stats_service import StatsService
from app.keyboards.keyboards import main_menu_keyboard

router = Router()

# Admin user IDs (replace with actual admin Telegram IDs)
ADMIN_IDS = [123456789]

class AdminState(StatesGroup):
    waiting_for_csv = State()
    waiting_for_broadcast_message = State()

def is_admin(user_id: int) -> bool:
    """Check if the user is an admin"""
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    """Show admin menu if the user is an admin"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📊 User Statistics")],
            [types.KeyboardButton(text="📝 Upload Words CSV")],
            [types.KeyboardButton(text="📣 Broadcast Message")],
            [types.KeyboardButton(text="🔙 Back to Main Menu")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📊 Admin Panel\n\n"
        "What would you like to do?",
        reply_markup=keyboard
    )

@router.message(F.text == "📊 User Statistics")
async def admin_stats(message: types.Message, session: AsyncSession):
    """Show statistics for all users"""
    if not is_admin(message.from_user.id):
        return
    
    stats_service = StatsService(session)
    users_stats = await stats_service.get_all_users_stats()
    
    if not users_stats:
        await message.answer("No users found.")
        return
    
    # Format stats
    response = "📊 <b>User Statistics</b>\n\n"
    for i, user in enumerate(users_stats, 1):
        response += (
            f"{i}. <b>{user['name']}</b>\n"
            f"   Language: {user['language']}, Level: {user['level']}\n"
            f"   Words: {user['words_count']}\n\n"
        )
    
    await message.answer(response, parse_mode="HTML")

@router.message(F.text == "📝 Upload Words CSV")
async def request_csv(message: types.Message, state: FSMContext):
    """Request CSV file with words"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "Please upload a CSV file with words in the following format:\n\n"
        "word,translation,example,level,language,audio_url\n\n"
        "Example:\n"
        "apple,яблоко,I eat an apple every day.,A1,english,http://example.com/audio.mp3\n\n"
        "Audio URL is optional."
    )
    
    await state.set_state(AdminState.waiting_for_csv)

@router.message(AdminState.waiting_for_csv, F.document)
async def process_csv(message: types.Message, state: FSMContext, session: AsyncSession):
    """Process uploaded CSV file with words"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    # Download the file
    file = await message.bot.get_file(message.document.file_id)
    file_content = await message.bot.download_file(file.file_path)
    
    # Process CSV
    try:
        csv_content = file_content.read().decode('utf-8')
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.reader(csv_file)
        
        # Skip header
        next(csv_reader, None)
        
        # Insert words
        words_added = 0
        for row in csv_reader:
            if len(row) < 5:
                continue  # Skip invalid rows
            
            word, translation, example, level, language = row[:5]
            audio_url = row[5] if len(row) > 5 else None
            
            # Check if word already exists
            result = await session.execute(
                select(Word).where(
                    Word.word == word,
                    Word.language == language
                )
            )
            existing_word = result.scalars().first()
            
            if existing_word:
                continue  # Skip existing words
            
            # Insert new word
            await session.execute(
                insert(Word).values(
                    word=word,
                    translation=translation,
                    example=example,
                    level=level,
                    language=language,
                    audio_url=audio_url
                )
            )
            words_added += 1
        
        await session.commit()
        
        await message.answer(f"CSV processed successfully. Added {words_added} new words.")
    except Exception as e:
        await message.answer(f"Error processing CSV: {str(e)}")
    
    await state.clear()

@router.message(F.text == "📣 Broadcast Message")
async def request_broadcast(message: types.Message, state: FSMContext):
    """Request broadcast message"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "Enter the message you want to send to all users:"
    )
    
    await state.set_state(AdminState.waiting_for_broadcast_message)

@router.message(AdminState.waiting_for_broadcast_message)
async def send_broadcast(message: types.Message, state: FSMContext, session: AsyncSession):
    """Send broadcast message to all users"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    # Get all users
    result = await session.execute(select(Word.telegram_id))
    user_ids = [row[0] for row in result.all()]
    
    # Send message to all users
    sent_count = 0
    for user_id in user_ids:
        try:
            await message.bot.send_message(
                user_id,
                f"📣 <b>Announcement</b>\n\n{message.text}",
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception:
            continue
    
    await message.answer(f"Message sent to {sent_count} users.")
    await state.clear() 