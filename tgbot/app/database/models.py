from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class LanguageEnum(enum.Enum):
    ENGLISH = "english"
    GERMAN = "german"

class LevelEnum(enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    language = Column(String(20), nullable=False)
    level = Column(String(5), nullable=False)
    date_joined = Column(DateTime, default=datetime.utcnow)
    
    words = relationship("UserWord", back_populates="user")
    settings = relationship("Settings", uselist=False, back_populates="user")

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(100), nullable=False)
    example = Column(Text)
    level = Column(String(5), nullable=False)
    language = Column(String(20), nullable=False)
    audio_url = Column(String(255), nullable=True)
    
    user_words = relationship("UserWord", back_populates="word")

class UserWord(Base):
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    added_date = Column(DateTime, default=datetime.utcnow)
    next_review = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=1))
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="words")
    word = relationship("Word", back_populates="user_words")

class Settings(Base):
    __tablename__ = "settings"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    notify = Column(Boolean, default=True)
    words_per_day = Column(Integer, default=5)
    language = Column(String(20), nullable=False)
    
    user = relationship("User", back_populates="settings") 