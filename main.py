import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=15)
        # Создаем таблицу, если ее нет
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                name TEXT,
                age INTEGER,
                drink TEXT,
                about TEXT,
                photo_id TEXT,
                lat FLOAT,
                lon FLOAT
            )
        ''')
        await conn.close()
        print("Связь с базой Supabase установлена! ✅")
    except Exception as e:
        print(f"Ошибка подключения к базе: {e}")

# --- НОВАЯ ФУНКЦИЯ (Которую искал бот) ---

async def get_user(user_id):
    """Получает данные одного пользователя по его ID"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # fetchrow возвращает одну строку (запись) или None
        row = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        return row
    finally:
        await conn.close()

# --- ПРОВЕРКА СУЩЕСТВОВАНИЯ ---

async def user_exists(user_id):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        user = await conn.fetchrow('SELECT user_id FROM users WHERE user_id = $1', user_id)
        return user is not None
    finally:
        await conn.close()

# --- ФУНКЦИИ ПОИСКА ---

async def get_users_nearby(exclude_user_id, lat, lon):
    """Поиск людей в радиусе (delta)"""
    delta = 0.08  # Примерно 8-10 км
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow('''
            SELECT user_id, name, age, drink, photo_id, about, lat, lon 
            FROM users 
            WHERE user_id != $1 
              AND lat BETWEEN $2 - $4 AND $2 + $4
              AND lon BETWEEN $3 - $4 AND $3 + $4
            ORDER BY RANDOM() 
            LIMIT 1
        ''', exclude_user_id, lat, lon, delta)
        return row
    finally:
        await conn.close()

async def get_all_users(exclude_user_id):
    """Поиск 'Везде'"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow('''
            SELECT user_id, name, age, drink, photo_id, about, lat, lon 
            FROM users 
            WHERE user_id != $1 
            ORDER BY RANDOM() 
            LIMIT 1
        ''', exclude_user_id)
        return row
    finally:
        await conn.close()

# --- СОХРАНЕНИЕ ---

async def save_user(user_id, data):
    """Сохраняет профиль (включая координаты)"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            INSERT INTO users (user_id, name, age, drink, about, photo_id, lat, lon)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id) DO UPDATE 
            SET name = EXCLUDED.name, age = EXCLUDED.age, drink = EXCLUDED.drink, 
                about = EXCLUDED.about, photo_id = EXCLUDED.photo_id,
                lat = EXCLUDED.lat, lon = EXCLUDED.lon
        ''', user_id, data.get('name'), data.get('age'), data.get('drink'), 
             data.get('about'), data.get('photo_id'), data.get('lat'), data.get('lon'))
    finally:
        await conn.close()

async def add_like(liker_id, liked_id):
    """Записывает лайк и проверяет на взаимность"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('CREATE TABLE IF NOT EXISTS likes (liker_id BIGINT, liked_id BIGINT)')
        await conn.execute('INSERT INTO likes (liker_id, liked_id) VALUES ($1, $2)', liker_id, liked_id)
        
        match = await conn.fetchval('SELECT 1 FROM likes WHERE liker_id = $1 AND liked_id = $2', liked_id, liker_id)
        return match is not None
    finally:
        await conn.close()