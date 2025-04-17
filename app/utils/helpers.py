import random
from datetime import datetime, timedelta
from typing import List, Tuple

def format_word_card(word, translation, example, audio_url=None):
    """Format a word card for display"""
    card = f"📝 <b>{word}</b>\n\n"
    card += f"🔤 <i>{translation}</i>\n\n"
    
    if example:
        card += f"💬 Example:\n<i>{example}</i>\n\n"
    
    if audio_url:
        card += "🔊 Listen to pronunciation"
    
    return card

def format_user_stats(stats):
    """Format user statistics for display"""
    result = "📊 <b>Your Learning Stats</b>\n\n"
    result += f"📚 Total words: {stats['total_words']}\n"
    result += f"🔄 Words to review today: {stats['words_to_review']}\n"
    result += f"✅ Accuracy: {stats['accuracy']}%\n"
    result += f"📈 Words added last week: {stats['words_added_last_week']}\n\n"
    
    if stats['recent_words']:
        result += "🔍 <b>Recently added words:</b>\n"
        for word, translation, review_count in stats['recent_words']:
            result += f"• {word} - {translation} (reviewed {review_count} times)\n"
    
    return result

def generate_fill_in_blank(example, word):
    """Generate a fill in the blank exercise from an example sentence"""
    if not example or word not in example:
        # If word doesn't appear in example or no example exists, create a simple sentence
        return f"Please translate: '{word}'", word
    
    # Replace the word with blank
    blank_length = min(len(word), 10)  # Cap the blank length
    blank = "_" * blank_length
    exercise = example.replace(word, blank)
    
    return exercise, word

def generate_options(correct_word, other_words, count=4):
    """Generate multiple choice options with one correct answer"""
    options = [correct_word.translation]
    
    # Add other options, avoiding duplicates
    available_words = [w for w in other_words if w.translation != correct_word.translation]
    if len(available_words) >= count - 1:
        chosen = random.sample(available_words, count - 1)
        options.extend([w.translation for w in chosen])
    else:
        # If not enough words, use what we have
        options.extend([w.translation for w in available_words])
    
    # Shuffle options
    random.shuffle(options)
    
    return options, options.index(correct_word.translation)

def calculate_next_notification_time():
    """Calculate next notification time (for reminders)"""
    now = datetime.utcnow()
    
    # Default to next day at 10 AM
    next_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if next_time <= now:
        next_time += timedelta(days=1)
    
    return next_time 