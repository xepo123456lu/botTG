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
from handlers import registration, profile, search, common
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

async def run_once_broadcast(bot: Bot) -> None:
    """
    Временная рассылка в рамках отладки/исправления бага.
    """
    text = """Привет подружка! ✨



В приложении был баг, что текст который отправляли под аватаркой доходил до пользователя но они не могла открыть чат. 🌸



Если твой вопрос остался без ответа — отправь его ещё раз, теперь чат откроется корректно. Приятного общения!"""

    try:
        conn = await asyncpg.connect(database.DATABASE_URL, timeout=15)
        try:
            rows = await conn.fetch("SELECT user_id FROM users")
            user_ids = [int(r["user_id"]) for r in rows]
        finally:
            await conn.close()
    except Exception:
        return

    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
        except Exception:
            # Не прерываем рассылку, если бот заблокировали/пользователь недоступен.
            pass
        await asyncio.sleep(0.05)

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

    # УДАЛИТЬ ЭТОТ БЛОК ПОСЛЕ ТОГО, КАК ПОЛУЧИШЬ СООБЩЕНИЕ В БОТЕ
    async def on_startup(*args, **kwargs):
        # aiogram может передать bot в аргументах/kwargs
        bot_from_args = next((a for a in args if isinstance(a, Bot)), None)
        bot_from_kwargs = kwargs.get("bot")
        await run_once_broadcast(bot_from_kwargs or bot_from_args or bot)

    dp.startup.register(on_startup)

    # Роутеры
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)
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