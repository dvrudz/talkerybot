import asyncio
import csv
import os
from sqlalchemy import insert
from dotenv import load_dotenv

from app.database.models import Word
from app.database.db import async_session

# Sample words for English A1 level
ENGLISH_A1_WORDS = [
    ["apple", "яблоко", "I eat an apple every day.", "A1", "english", None],
    ["book", "книга", "I read a book before sleep.", "A1", "english", None],
    ["cat", "кот", "The cat is sleeping on the sofa.", "A1", "english", None],
    ["dog", "собака", "My dog likes to play in the park.", "A1", "english", None],
    ["house", "дом", "We live in a small house.", "A1", "english", None],
    ["water", "вода", "I drink a lot of water every day.", "A1", "english", None],
    ["bread", "хлеб", "She buys fresh bread every morning.", "A1", "english", None],
    ["friend", "друг", "He is my best friend.", "A1", "english", None],
    ["car", "машина", "My father has a new car.", "A1", "english", None],
    ["school", "школа", "Children go to school every day.", "A1", "english", None]
]

# Sample words for German A1 level
GERMAN_A1_WORDS = [
    ["Apfel", "яблоко", "Ich esse jeden Tag einen Apfel.", "A1", "german", None],
    ["Buch", "книга", "Ich lese ein Buch vor dem Schlafengehen.", "A1", "german", None],
    ["Katze", "кот", "Die Katze schläft auf dem Sofa.", "A1", "german", None],
    ["Hund", "собака", "Mein Hund spielt gerne im Park.", "A1", "german", None],
    ["Haus", "дом", "Wir wohnen in einem kleinen Haus.", "A1", "german", None],
    ["Wasser", "вода", "Ich trinke jeden Tag viel Wasser.", "A1", "german", None],
    ["Brot", "хлеб", "Sie kauft jeden Morgen frisches Brot.", "A1", "german", None],
    ["Freund", "друг", "Er ist mein bester Freund.", "A1", "german", None],
    ["Auto", "машина", "Mein Vater hat ein neues Auto.", "A1", "german", None],
    ["Schule", "школа", "Kinder gehen jeden Tag zur Schule.", "A1", "german", None]
]

# Function to insert words
async def insert_words():
    load_dotenv()
    
    async with async_session() as session:
        # First check if words already exist
        result = await session.execute("SELECT COUNT(*) FROM words")
        count = result.scalar()
        
        if count > 0:
            print(f"Database already has {count} words, skipping insertion")
            return
        
        # Add English words
        for word_data in ENGLISH_A1_WORDS:
            word, translation, example, level, language, audio_url = word_data
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
        
        # Add German words
        for word_data in GERMAN_A1_WORDS:
            word, translation, example, level, language, audio_url = word_data
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
        
        await session.commit()
        print("Sample words inserted successfully")

# Function to export words to CSV
def export_words_to_csv():
    # Create a CSV file with all sample words
    all_words = ENGLISH_A1_WORDS + GERMAN_A1_WORDS
    
    with open('sample_words.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['word', 'translation', 'example', 'level', 'language', 'audio_url'])
        writer.writerows(all_words)
    
    print("Sample words exported to sample_words.csv")

if __name__ == "__main__":
    # Insert words into database
    asyncio.run(insert_words())
    
    # Export words to CSV for reference
    export_words_to_csv() 