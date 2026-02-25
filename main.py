import logging
import asyncio
from aiogram import Bot, Dispatcher
from database import init_db
from handlers import registration, search, profile # Импортируем наши модули
import os
from dotenv import load_dotenv
# (или та библиотека, которую ты используешь)

# 1. Загружаем переменные из .env
load_dotenv()

# 2. Достаем именно API_TOKEN (регистр важен!)
TOKEN = os.getenv("API_TOKEN")

# 3. Проверяем, что он нашелся, прежде чем запускать бота
if not TOKEN:
    print("Ошибка: Переменная API-token не найдена в .env!")
    exit()


bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- РЕГИСТРАЦИЯ РОУТЕРОВ ---
# Важно: registration.router должен быть первым, 
# чтобы команда /start обрабатывалась корректно
dp.include_router(registration.router)
dp.include_router(search.router)
dp.include_router(profile.router)

async def main():
    # Инициализируем базу данных (создаем таблицы, если их нет)
    await init_db()
    
    # Удаляем все накопленные сообщения, пока бот был выключен
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем бесконечный опрос
    print("Бот запущен и готов к работе! 🚀")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()