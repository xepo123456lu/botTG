import os
import asyncio
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import asyncpg

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties 

import database
from handlers import registration, profile, search, common, moderation
from viewed_storage import init_viewed_db

load_dotenv()

# --- 1. ВЕБ-СЕРВЕР ДЛЯ ПОРТА RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. ОСНОВНОЙ КОД БОТА ---
BOT_TOKEN = os.getenv("API_TOKEN")



async def main():
    # Запускаем Flask
    Thread(target=run_flask, daemon=True).start()

    if not BOT_TOKEN:
        print("ОШИБКА: API_TOKEN не найден!")
        return

    # Правильное создание бота для aiogram 3.x
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()

    
    

    # Роутеры
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)
    dp.include_router(moderation.router)
    dp.include_router(common.router)

    # База данных
    await database.init_db()
    await init_viewed_db()
    
    print("Бот успешно запущен ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")