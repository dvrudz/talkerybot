from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Registration keyboards
def language_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🇬🇧 English"), KeyboardButton("🇩🇪 German"))
    return keyboard

def level_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("A1"), KeyboardButton("A2"))
    keyboard.add(KeyboardButton("B1"), KeyboardButton("B2"))
    return keyboard

# Main menu keyboard
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Learn New Words"))
    keyboard.add(KeyboardButton("🔄 Training"), KeyboardButton("📋 My Words"))
    keyboard.add(KeyboardButton("📊 My Progress"), KeyboardButton("⚙️ Settings"))
    return keyboard

# Word learning keyboards
def word_card_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⏭️ Next Word", callback_data="next_word"),
        InlineKeyboardButton("➕ Add to My Words", callback_data="add_word"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    return keyboard

def my_words_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("❌ Remove Word", callback_data="remove_word"),
        InlineKeyboardButton("⏭️ Next Word", callback_data="next_my_word"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    return keyboard

# Training keyboards
def training_options_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔤 Translation Quiz"), KeyboardButton("📝 Fill in the Blank"))
    keyboard.add(KeyboardButton("🔙 Back to Menu"))
    return keyboard

def quiz_answer_keyboard(answers) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, answer in enumerate(answers):
        keyboard.add(InlineKeyboardButton(answer, callback_data=f"answer_{i}"))
    return keyboard

# Settings keyboards
def settings_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Change Language"))
    keyboard.add(KeyboardButton("📊 Change Words Per Day"))
    keyboard.add(KeyboardButton("🔔 Toggle Notifications"))
    keyboard.add(KeyboardButton("🔄 Reset Progress"))
    keyboard.add(KeyboardButton("🔙 Back to Menu"))
    return keyboard

def words_per_day_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(3, 16):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"words_per_day_{i}"))
    keyboard.add(*buttons)
    return keyboard

def yes_no_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Yes", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ No", callback_data="confirm_no")
    )
    return keyboard

# Review keyboard
def review_now_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📝 Review Now", callback_data="review_now"))
    return keyboard 