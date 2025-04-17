"""Initial database setup

Revision ID: 0001
Revises: 
Create Date: 2023-04-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.Column('level', sa.String(length=5), nullable=False),
        sa.Column('date_joined', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    
    # Create words table
    op.create_table('words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.Column('translation', sa.String(length=100), nullable=False),
        sa.Column('example', sa.Text(), nullable=True),
        sa.Column('level', sa.String(length=5), nullable=False),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.Column('audio_url', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_words table
    op.create_table('user_words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('added_date', sa.DateTime(), nullable=True),
        sa.Column('next_review', sa.DateTime(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create settings table
    op.create_table('settings',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notify', sa.Boolean(), nullable=True),
        sa.Column('words_per_day', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('settings')
    op.drop_table('user_words')
    op.drop_table('words')
    op.drop_table('users') 