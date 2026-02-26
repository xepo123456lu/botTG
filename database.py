import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    try:
        # Увеличиваем таймаут, так как пулер может отвечать чуть дольше
        conn = await asyncpg.connect(DATABASE_URL, timeout=15)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                name TEXT,
                age INTEGER,
                drink TEXT,
                about TEXT,
                photo_id TEXT
            )
        ''')
        await conn.close()
        print("Связь с базой Supabase (через Pooler) установлена! ✅")
    except Exception as e:
        print(f"Ошибка подключения к базе: {e}")

async def user_exists(user_id):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        user = await conn.fetchrow('SELECT user_id FROM users WHERE user_id = $1', user_id)
        return user is not None
    finally:
        await conn.close()

async def save_user(user_id, data):
    """Сохраняет профиль в Supabase"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            INSERT INTO users (user_id, name, age, drink, about, photo_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE 
            SET name = EXCLUDED.name, age = EXCLUDED.age, drink = EXCLUDED.drink, 
                about = EXCLUDED.about, photo_id = EXCLUDED.photo_id
        ''', user_id, data.get('name'), data.get('age'), data.get('drink'), data.get('about'), data.get('photo'))
    finally:
        await conn.close()

async def get_users_nearby(exclude_user_id, lat, lon):
    """Тот самый поиск людей рядом (твоя логика с delta)"""
    delta = 0.08  # твои ~5-7 км
    
    # Ищем в MongoDB по диапазону координат
    query = {
        "user_id": {"$ne": exclude_user_id},
        "lat": {"$gte": lat - delta, "$lte": lat + delta},
        "lon": {"$gte": lon - delta, "$lte": lon + delta}
    }
    
    # Берем случайного пользователя (как ORDER BY RANDOM() в SQL)
    pipeline = [
        {"$match": query},
        {"$sample": {"size": 1}}
    ]
    
    cursor = users_collection.aggregate(pipeline)
    users = await cursor.to_list(length=1)
    return users[0] if users else None

async def add_like(liker_id, liked_id):
    """Записывает лайк в базу"""
    await likes_collection.update_one(
        {"liker_id": liker_id, "liked_id": liked_id},
        {"$set": {"liker_id": liker_id, "liked_id": liked_id}},
        upsert=True
    )

async def get_user(user_id):
    """Просто получить данные анкеты"""
    return await users_collection.find_one({"user_id": user_id})