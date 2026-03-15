import os
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

import database
from handlers import registration, profile, search

# --- 1. ВЕБ-СЕРВЕР ДЛЯ ПОРТА RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    # Render передает порт в переменную PORT. Если ее нет, берем 8080.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. ОСНОВНОЙ КОД БОТА ---
# В Render переменная называется API_TOKEN (судя по твоим скринам)
BOT_TOKEN = os.getenv("API_TOKEN")

async def main():
    # Запускаем Flask в отдельном потоке, чтобы он не мешал боту
    Thread(target=run_flask, daemon=True).start()

    if not BOT_TOKEN:
        print("ОШИБКА: API_TOKEN не найден в переменных окружения!")
        return

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)

    # Инициализируем базу данных
    await database.init_db()
    
    print("Бот успешно запущен и порт открыт ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")