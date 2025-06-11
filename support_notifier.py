# support_notifier.py
import os
import json
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=BOT_TOKEN)

SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

def send_daily_support():
    message = (
        "🌿 Психологическая поддержка:\n"
        "Сегодня — хороший день, чтобы позаботиться о себе. Сделай паузу, отдохни, "
        "подыши глубоко. Ты справишься 💪"
    )
    for user_id in load_subscribers():
        try:
            bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Ошибка отправки {user_id}: {e}")

if __name__ == "__main__":
    send_daily_support()
