import os
import asyncio
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

import database
from handlers import registration, profile, search

load_dotenv()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (БЕЗ НЕГО БОТ УПАДЕТ) ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    # Render сам назначит порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ОСНОВНОЙ КОД БОТА ---
BOT_TOKEN = os.getenv("API_TOKEN") # В Render у тебя написано API_TOKEN
if not BOT_TOKEN:
    raise SystemExit("Не задан BOT_TOKEN/API_TOKEN в Environment Variables.")

async def main():
    # Запускаем веб-сервер в отдельном потоке
    Thread(target=run_flask).start()

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)

    await database.init_db()
    print("Бот запущен ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())