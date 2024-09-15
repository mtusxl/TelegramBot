FROM python:3.8-slim

RUN pip install pyTelegramBotAPI redis python-dotenv sqlalchemy pytest


COPY . /TelegramBot

WORKDIR /TelegramBot

VOLUME /var/lib/database/data


CMD ["python", "main.py"]
