import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from models import Base, User, Word, Category, Schedule

class TestDatabaseModels(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Создаем движок и таблицы
        cls.engine = create_engine('sqlite:///flashcards.db')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        # Каждый тест будет иметь новую сессию
        self.session = self.Session()

    def tearDown(self):
        # Завершение сессии после каждого теста
        self.session.close()

    def test_user_fields(self):
        # Создаем тестового пользователя
        new_user = User(user_id=1)
        self.session.add(new_user)
        self.session.commit()

        # Извлекаем пользователя и проверяем поля
        user = self.session.query(User).filter_by(user_id=1).one()
        self.assertEqual(user.user_id, 1)

    def test_word_fields(self):
        # Создаем тестовые данные
        new_user = User(user_id=1)
        new_word = Word(word_id=1, user_id=1, word='hello', translation='привет', category_id=1)
        self.session.add(new_user)
        self.session.add(new_word)
        self.session.commit()

        # Извлекаем слово и проверяем поля
        word = self.session.query(Word).filter_by(word_id=1).one()
        self.assertEqual(word.word_id, 1)
        self.assertEqual(word.user_id, 1)
        self.assertEqual(word.word, 'hello')
        self.assertEqual(word.translation, 'привет')
        self.assertEqual(word.category_id, 1)

    def test_category_fields(self):
        # Создаем тестовые данные
        new_user = User(user_id=1)
        new_category = Category(user_id=1, category_id=1, category_name='greetings')
        self.session.add(new_user)
        self.session.add(new_category)
        self.session.commit()

        # Извлекаем категорию и проверяем поля
        category = self.session.query(Category).filter_by(category_id=1).one()
        self.assertEqual(category.user_id, 1)
        self.assertEqual(category.category_id, 1)
        self.assertEqual(category.category_name, 'greetings')

    def test_schedule_fields(self):
        # Создаем тестовые данные
        new_user = User(user_id=1)
        new_word = Word(word_id=1, user_id=1, word='hello', translation='привет', category_id=1)
        new_schedule = Schedule(schedule_id=1, user_id=1, word_id=1, next_review_date=date.today(), repetition_interval=7)
        self.session.add(new_user)
        self.session.add(new_word)
        self.session.add(new_schedule)
        self.session.commit()

        # Извлекаем расписание и проверяем поля
        schedule = self.session.query(Schedule).filter_by(schedule_id=1).one()
        self.assertEqual(schedule.schedule_id, 1)
        self.assertEqual(schedule.user_id, 1)
        self.assertEqual(schedule.word_id, 1)
        self.assertEqual(schedule.next_review_date, date.today())
        self.assertEqual(schedule.repetition_interval, 7)

if __name__ == '__main__':
    unittest.main()
