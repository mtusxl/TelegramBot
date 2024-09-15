import os
from dotenv import load_dotenv
import telebot

from telebot import types
from telebot.types import Message

import redis

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Word, Category, Schedule


import time
import datetime

import json




intervals = [
    datetime.timedelta(minutes=2),
    datetime.timedelta(minutes=20),
    datetime.timedelta(hours=1),
    datetime.timedelta(hours=6),
    datetime.timedelta(days=1),
    datetime.timedelta(days=3),
    datetime.timedelta(days=7),
    datetime.timedelta(days=14),
    datetime.timedelta(days=30)
]





redis_client = redis.StrictRedis(host='redis', port="6379", db=0, decode_responses=True)
def save__in_redis(user_id, key, value):
    redis_client.hset(user_id, key, value)
    redis_client.expire(user_id, 3600)

def get_from_redis(user_id, key):
    return redis_client.hget(user_id, key)


def del_redis_values(user_id, key):
    keys = redis_client.keys(f"{user_id}_*")

    redis_client.delete(key)




def open_session(func):
    def wrapper(*args, **kwargs):
        engine = create_engine('sqlite:///flashcards.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as ex:
            session.rollback()
            raise ex
        finally:
            session.close()
    return wrapper

@open_session
def check_users(session, id):
    if session.query(User).filter(User.user_id == id).first():
        return True
    else: return False

@open_session
def add_new_user(session, id):
    try:
        new_user = User(user_id=id)
        session.add(new_user)
        session.commit()
    finally:
        session.close()
    
@open_session
def update_user_words(session, user_id, new_words:list):
    user = session.query(User).filter(User.user_id == user_id).first()
    if user:
        user.words.extend(new_words)
        session.commit()
        return True
    else:
        return False

@open_session
def update_user_schedule(session, id, new_schedule):
    user = session.query(User).filter(User.user_id == id).first()
    if user:
        user.schedule.extend(new_schedule)
        session.commit()
        return True
    else:
        return False

@open_session
def get_words(session, user_id):
    words = session.query(Word).filter_by(user_id=user_id).all()
    list_words = [word.word for word in words if word.word]
    return list_words

@open_session
def add_word(session, user_id, word, category_id):
    new_word = Word(user_id=user_id, word=word, category_id=category_id)
    session.add(new_word)
    session.commit()
    return new_word.word_id


@open_session
def get_translation(session, user_id):
    words = session.query(Word).filter_by(user_id=user_id).all()
    list_words = [word.translation for word in words if word.translation]
    return list_words

@open_session
def add_translation(session, word, translation):
    word_entry = session.query(Word).filter_by(word=word).first()
    if word_entry:
        word_entry.translation = translation
        session.commit()

@open_session
def get_categorize_list(session, user_id):
    categories = session.query(Category).filter_by(user_id=user_id).all()
    return [category.category_name for category in categories]

@open_session
def add_name_categorize(session, user_id, name):
    new_category = Category(user_id=user_id, category_name=name)
    session.add(new_category)
    session.commit()

@open_session
def del_categorize(session, user_id, name_categorize):
    delete_to_categorize = session.query(Category).filter(Category.category_name == name_categorize, Category.user_id == user_id).first()
    if delete_to_categorize:
        session.delete(delete_to_categorize)
        session.commit()
        return True
    else:
        return False

@open_session
def edit_categorize(session, user_id, old_name, new_name):
    old_category = session.query(Category).filter(Category.user_id == user_id, Category.category_name == old_name).first()
    if old_category:
        old_category.category_name = new_name
        session.commit()
        return True
    else:
        return False

@open_session
def get_words_by_category(session, user_id, name_categorize):
    category = session.query(Category).filter(Category.user_id == user_id, Category.category_name == name_categorize).first()
    if not category:
        return False
    words = session.query(Word).filter(Word.user_id == user_id, Word.category_id == category.category_id).all()
    return [(word.word, word.translation) for word in words]

TOKEN = ("7197502789:AAFJ_qhO73iuacnZ9RCJsaWMm_l5_Vjn_CQ")
lan = {}

def main():
    bot = telebot.TeleBot(TOKEN)
    

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        bot.reply_to(message, "Привет! Я бот для изучения иностранных слов. Отправь мне слова, а я помогу тебе их выучить.")
        id = message.chat.id
        if check_users(id=id)==False:
            add_new_user(id=id)
        
        

    @bot.message_handler(commands=['new_categorize'])
    def add_new_categorize(message):
        bot.send_message(message.chat.id, "Как будет называться новая категория для слов: ")
        bot.register_next_step_handler(message, new_categorize)

    @open_session
    def new_categorize(session, message):
        try:
            name_cat = message.text
            if name_cat in get_categorize_list(user_id=message.from_user.id):
                bot.send_message(message.chat.id, "Такая категория уже существует!")
            else:
                bot.send_message(message.chat.id, f"Ваша новая категория будет называться: {name_cat}")
                add_name_categorize(user_id=message.from_user.id, name=name_cat)
        except Exception as ex:
            bot.send_message(message.chat.id, f"Произошла какая-то ошибка: {ex}")

    @bot.message_handler(commands=['categorizes'])
    def categories_handler(message):
        try:
            id = message.from_user.id
            len_cat = len(get_categorize_list(user_id=id))
            if len_cat > 0:
                markup = types.ReplyKeyboardMarkup(row_width=len_cat, one_time_keyboard=True)
                rows = [get_categorize_list(user_id=id)[i:i+3] for i in range(0, len_cat, 3)]
                for row in rows:
                    markup.add(*[types.KeyboardButton(button) for button in row])
                bot.send_message(message.chat.id, "Выберите категорию", reply_markup=markup)
                bot.register_next_step_handler(message, Button_Events)
            else:
                bot.send_message(message.chat.id, "У вас нет никаких категорий. Создайте новую категорию с помощью команды /new_categorize.")
        except Exception as ex:
            bot.send_message(message.chat.id, f"Произошла какая-то ошибка: {ex}")

    def Button_Events(message):
        if message.text in get_categorize_list(user_id=message.from_user.id):
            markup = types.InlineKeyboardMarkup()
            edit_btn = types.InlineKeyboardButton("Изменить название категории", callback_data="edit")
            markup.row(edit_btn)
            delete_btn = types.InlineKeyboardButton("Удалить категорию", callback_data="delete")
            view_btn = types.InlineKeyboardButton("Посмотреть слова в категории", callback_data="view_words")
            markup.row(delete_btn, view_btn)
            tests_btn = types.InlineKeyboardButton("Изучить слова", callback_data="tests")
            back_btn = types.InlineKeyboardButton("Назад", callback_data="back")
            markup.row(tests_btn, back_btn)
            bot.send_message(message.chat.id, "Выберите действие: ", reply_markup=markup)

    @bot.callback_query_handler(func=lambda callback: True)
    def callback_messages(callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        category_to_del = callback.message.message_id - 1
        previous_message_text = bot.forward_message(chat_id, chat_id, category_to_del).text
        
        if callback.data == "delete":
            del_def = del_categorize(user_id=user_id, name_categorize=previous_message_text)
            if del_def:
                bot.send_message(chat_id, f"Категория '{previous_message_text}' была успешно удалена")
            else:
                bot.send_message(chat_id, f"Ошибка: Категория '{previous_message_text}' не была удалена")
        
        if callback.data == "edit":
            bot.send_message(chat_id, "Введите новое название категории:")
            bot.register_next_step_handler(callback.message, add_new_name_categorize, previous_message_text)

        if callback.data == "view_words":
            words = get_words_by_category(user_id=user_id, name_categorize=previous_message_text)
            bot.send_message(callback.message.chat.id, "Слова:")
            if words:
                for word, translation in words:
                    bot.send_message(callback.message.chat.id, f"{word} - {translation}\n")
            else:
                bot.send_message(callback.message.chat.id, "Категория пуста. Добавьте слова в категорию с помощью команды /add_word")

    def add_new_name_categorize(message, old_category_name):
        chat_id = message.chat.id
        user_id = message.from_user.id
        new_name = message.text

        edit_def = edit_categorize(user_id=user_id, old_name=old_category_name, new_name=new_name)

        if edit_def:
            bot.send_message(chat_id, f"Название категории было изменено на '{new_name}'")
        else:
            bot.send_message(chat_id, f"Категория не была изменена по каким-то причинам")

    @bot.message_handler(commands=['add_word'])
    def new_word(message):
        id = message.from_user.id
        len_cat = len(get_categorize_list(user_id=id))
        if len_cat > 0:
            markup = types.ReplyKeyboardMarkup(row_width=len_cat, one_time_keyboard=True)
            rows = [get_categorize_list(user_id=id)[i:i+3] for i in range(0, len_cat, 3)]
            for row in rows:
                markup.add(*[types.KeyboardButton(button) for button in row])
            bot.send_message(message.chat.id, "В какую категорию добавить новое слово?", reply_markup=markup)
            bot.register_next_step_handler(message, how_categorize)
        else:
            bot.send_message(message.chat.id, "У вас нет никаких категорий. Создайте новую категорию с помощью команды /new_categorize.")

    @open_session
    def how_categorize(session, message):
        category_id = session.query(Category).filter_by(category_name=message.text).first().category_id
        save__in_redis(message.chat.id, "Category_id", int(category_id))

        if message.text in get_categorize_list(user_id=message.from_user.id):
            bot.send_message(message.chat.id, "Введите слово на родном языке")
            bot.register_next_step_handler(message, after_answer)
        else:
            bot.send_message(message.chat.id, "Такой категории не существует. Создайте ее с помощью команды /new_categorize")

    @open_session
    def after_answer(session, message):
        word = message.text
        category_id = get_from_redis(message.chat.id, "Category_id")

        save__in_redis(message.chat.id, "word", word)
        add_word(user_id=message.from_user.id, word=word, category_id=category_id)

        bot.send_message(message.chat.id, "Теперь введите слово на английском")
        bot.register_next_step_handler(message, English_word)

    @open_session
    def English_word(session, message):
        translation = message.text
        id = message.chat.id
        orig_word = get_from_redis(id, "word")
        word = session.query(Word).filter_by(word=orig_word).first().word
        add_translation(word=word, translation=translation)
        bot.send_message(message.chat.id, "Слово добавлено")

    @bot.message_handler(commands=['learned_words'])
    def learn_words(message):
        words_list = "".join([f"{i} - {j}\n" for i, j in zip(get_words(user_id=message.from_user.id), get_translation(user_id=message.from_user.id))])
        bot.send_message(message.chat.id, f"Слова: {words_list}")



    @bot.message_handler(commands=['learning_words'])
    def learning_words(message):
        id = message.from_user.id
        len_cat = len(get_categorize_list(user_id=id))
        if len_cat > 0:
            markup = types.ReplyKeyboardMarkup(row_width=len_cat, one_time_keyboard=True)
            rows = [get_categorize_list(user_id=id)[i:i+3] for i in range(0, len_cat, 3)]
            for row in rows:
                markup.add(*[types.KeyboardButton(button) for button in row])
            bot.send_message(message.chat.id, "Выбирете категорию изучаемых слов", reply_markup=markup)
            bot.register_next_step_handler(message, After_selecting)

    def After_selecting(message):
        category = message.text
        # Сохраняем категорию
        save__in_redis(message.chat.id, "Category_name", category)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(types.KeyboardButton(text="Далее"))
        
        bot.send_message(message.from_user.id, 'Повторите данные слова несколько раз и как повторите их нажмите кнопку "далее"', reply_markup=keyboard)

        words = get_words_by_category(message.chat.id, category)

        if words:
            message_text = "Слова: \n"
            for word, translation in words:
                message_text += f"{word} - {translation}\n"
            # Отправляем сообщение и сохраняем его ID
            message_words = bot.send_message(message.chat.id, message_text)
            # Используем правильное поле для сохранения ID сообщения
            save__in_redis(message.chat.id, "delete_after_reapeting", message_words.message_id)

    
    
        
    @bot.message_handler(func=lambda message: message.text == "Далее")
    def check_words_handler(message: types.Message):
        chat_id = message.chat.id
        category = get_from_redis(chat_id, "Category_name")
        
        # Получаем ID сообщения
        del_words = get_from_redis(chat_id, "delete_after_reapeting")

        if del_words:
            del_words = del_words.decode('utf-8')

            # Отправляем сообщение и удаляем по ID
            bot.send_message(chat_id, f"Удаляем сообщение с ID: {del_words}")
            bot.delete_message(chat_id, del_words)
        else:
            bot.send_message(chat_id, "Ошибка: не удалось найти сообщение для удаления.")
        
        # Получаем слова и их переводы
        words = get_words_by_category(chat_id, category)
        words_only = [word for word, translation in words]
        translation_words = [translation for word, translation in words]

        # Сериализация списков в строки JSON и сохранение в Redis
        redis_client.set(f"{chat_id}_words", json.dumps(words_only))
        redis_client.set(f"{chat_id}_translations", json.dumps(translation_words))
        redis_client.set(f"{chat_id}_current_index", 0)

        # Отправляем первое слово
        bot.send_message(chat_id, f"Переведите это слово: {words_only[0]}")
        bot.register_next_step_handler(message, check_translation)

    # Функция для проверки перевода
    def check_translation(message: types.Message):
        chat_id = message.chat.id
        user_translation = message.text

        # Получаем текущие слова и переводы из Redis
        words_only = json.loads(redis_client.get(f"{chat_id}_words"))
        translation_words = json.loads(redis_client.get(f"{chat_id}_translations"))
        current_index = int(redis_client.get(f"{chat_id}_current_index"))

        correct_translation = translation_words[current_index]

        if user_translation.lower() == correct_translation.lower():
            bot.send_message(chat_id, "Правильно!")
        else:
            bot.send_message(chat_id, f"Неправильно. Правильный перевод: {correct_translation}")
            # Добавляем неверный перевод в отдельный список для повторного тестирования
            redis_client.rpush(f"{chat_id}_incorrect_words", words_only[current_index])
            redis_client.rpush(f"{chat_id}_incorrect_translations", correct_translation)

        current_index += 1

        if current_index < len(words_only):
            # Обновляем текущий индекс и отправляем следующее слово
            redis_client.set(f"{chat_id}_current_index", current_index)
            bot.send_message(chat_id, f"Переведите это слово: {words_only[current_index]}")
            bot.register_next_step_handler(message, check_translation)
        else:
            # Заканчиваем проверку и начинаем проверку неверных слов
            redis_client.delete(f"{chat_id}_words")
            redis_client.delete(f"{chat_id}_translations")
            redis_client.delete(f"{chat_id}_current_index")

            incorrect_words = redis_client.lrange(f"{chat_id}_incorrect_words", 0, -1)

            if incorrect_words:
                bot.send_message(chat_id, "Мы проверили все слова, но на некоторые из них ты ответил неправильно, давай повторим слова, которые были неверно переведены.")
                check_incorrect_words(message=message, chat_id=chat_id)
            else:
                bot.send_message(chat_id, "Вы ответили правильно на все слова!")
                repetition_cycle(message=message)

    # Функция для проверки неверных слов
    def check_incorrect_words(message, chat_id):
        incorrect_words = redis_client.lrange(f"{chat_id}_incorrect_words", 0, -1)
        incorrect_translations = redis_client.lrange(f"{chat_id}_incorrect_translations", 0, -1)

        if incorrect_words:
            word = incorrect_words.pop(0)
            translation = incorrect_translations.pop(0)

            redis_client.ltrim(f"{chat_id}_incorrect_words", 1, -1)
            redis_client.ltrim(f"{chat_id}_incorrect_translations", 1, -1)

            bot.send_message(chat_id, f"Переведите это слово: {word}")
            bot.register_next_step_handler_by_chat_id(chat_id, lambda message: check_incorrect_translation(message, word, translation))
        else:
            bot.send_message(chat_id, "Все слова проверены!")
            repetition_cycle(message=message)

    def check_incorrect_translation(message: types.Message, word, correct_translation):
        chat_id = message.chat.id
        user_translation = message.text

        if user_translation.lower() == correct_translation.lower():
            bot.send_message(chat_id, "Правильно!")
        else:
            bot.send_message(chat_id, f"Неправильно. Правильный перевод: {correct_translation}")
            # Добавляем слово снова в очередь для повторного тестирования
            redis_client.rpush(f"{chat_id}_incorrect_words", word)
            redis_client.rpush(f"{chat_id}_incorrect_translations", correct_translation)

        check_incorrect_words(message, chat_id)

    def repetition_cycle(message: types.Message):
        intervals = [datetime.timedelta(seconds=30), datetime.timedelta(minutes=1), datetime.timedelta(hours=1), datetime.timedelta(days=1)]

        for interval in intervals:
            # Calculate next repetition time
            next_repetition = datetime.datetime.now() + interval

            # Format interval in a user-friendly way
            if interval.days >= 1:
                if interval.days == 1:
                    formatted_interval = f"{interval.days} день"
                else:
                    formatted_interval = f"{interval.days} дней"
            elif interval.seconds >= 3600:
                formatted_interval = f"{interval.seconds // 3600} часов"
            elif interval.seconds >= 60:
                formatted_interval = f"{interval.seconds // 60} минут"
            else:
                formatted_interval = f"{interval.seconds} секунд"

            # Send notification
            bot.send_message(message.chat.id, f"Следующее повторение будет через {formatted_interval}")

            # Wait until next repetition
            time.sleep(interval.total_seconds())

            # Send "Пора повторить слова!" message
            bot.send_message(message.chat.id, "Пора повторить слова!")

    bot.infinity_polling()
    telebot.logger.setLevel(telebot.logging.DEBUG)

if __name__ == "__main__":
    main()