from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship







DB_NAME = "flashcards.db"

engine = create_engine(f'sqlite:///{DB_NAME}')

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'

    user_id = Column(Integer, primary_key=True)
    words = relationship('Word', back_populates='user')
    schedule = relationship('Schedule', back_populates='users')

class Word(Base):
    __tablename__ = 'Word'

    word_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    word = Column(String)
    translation = Column(String)
    category_id = Column(Integer, ForeignKey("Categories.category_id"))
    
    category = relationship("Category", back_populates="words")
    user = relationship('User', back_populates='words')

class Category(Base):
    __tablename__ = 'Categories'

    user_id = Column(Integer, ForeignKey("Users.user_id"))
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(20))

    words = relationship('Word', back_populates="category")


class Schedule(Base):
    __tablename__ = 'Schedule'

    schedule_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    word_id = Column(Integer, ForeignKey("Word.word_id"))
    next_review_date = Column(Date)
    repetition_interval = Column(Integer)

    users = relationship("User", back_populates='schedule')


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
