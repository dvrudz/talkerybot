# TalkeryBot - Telegram Bot for Language Learning

A Telegram bot that helps users learn English and German vocabulary through flashcards, spaced repetition, and simple exercises.

## Features

- User registration with language and level selection
- Vocabulary learning with flashcards
- Training exercises (multiple choice, fill-in-the-blank)
- Spaced repetition algorithm for optimal memorization
- Progress tracking and statistics
- Custom settings for learning preferences

## Technical Requirements

- Python 3.10+
- PostgreSQL database
- Telegram Bot Token (from @BotFather)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/talkerybot.git
   cd talkerybot
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a PostgreSQL database for the bot.

6. Create a `.env` file with the following content:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   DATABASE_URL=postgresql+asyncpg://username:password@localhost/talkerybot
   ```
   Replace the placeholders with your actual Telegram Bot Token and database credentials.

7. Initialize the database:
   ```
   python init_db.py
   ```
   This will:
   - Create all required database tables
   - Import sample vocabulary for both languages

8. Run the bot:
   ```
   python bot.py
   ```

## Project Structure

- `bot.py` - Main entry point
- `init_db.py` - Database initialization script
- `sample_data.py` - Sample vocabulary data
- `app/` - Application code
  - `database/` - Database models and config
  - `handlers/` - Telegram bot handlers
  - `keyboards/` - Keyboard layouts
  - `services/` - Business logic
  - `utils/` - Helper functions

## Database Schema

The project uses PostgreSQL with the following tables:
- `Users` - user information and preferences
- `Words` - vocabulary with translations and examples
- `UserWords` - tracks learning progress for each word
- `Settings` - user preferences

## Admin Features

To access admin features, add your Telegram User ID to the `ADMIN_IDS` list in `app/handlers/admin.py`.

Admin features include:
- View statistics for all users
- Import vocabulary from CSV files
- Send broadcast messages to all users

## Customizing the Bot

### Adding More Vocabulary

You can add more vocabulary in two ways:

1. Update the sample data in `sample_data.py` and re-run `python sample_data.py`
2. Use the admin interface to upload a CSV file with words

### Custom Word Sets

To add specialized sets of vocabulary:
1. Create a CSV file with the following columns:
   ```
   word,translation,example,level,language,audio_url
   ```
2. Log in as admin and use the "Upload Words CSV" option

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 