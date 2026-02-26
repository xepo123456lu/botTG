import logging
import asyncio
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Импортируем ваши модули
from database import init_db
from handlers import registration, search, profile

# 1. Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("API_TOKEN")

if not TOKEN:
    print("Ошибка: Переменная API_TOKEN не найдена!")
    exit()

# --- БЛОК FLASK ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    # Render передает порт в переменную окружения PORT. Если её нет, используем 10000.
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Запускает Flask в отдельном потоке, чтобы он не мешал боту"""
    t = Thread(target=run_flask)
    t.daemon = True # Поток завершится вместе с основной программой
    t.start()

# --- НАСТРОЙКА БОТА ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Регистрация роутеров
dp.include_router(registration.router)
dp.include_router(search.router)
dp.include_router(profile.router)

async def main():
    # Инициализируем базу данных
    await init_db()
    
    # Очищаем очередь обновлений
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Бот запущен и готов к работе! 🚀")
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Сначала запускаем веб-сервер для Render
    keep_alive()
    
    # Затем запускаем основного бота
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен.")