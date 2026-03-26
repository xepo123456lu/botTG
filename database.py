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
                lon FLOAT,
                status TEXT DEFAULT 'pending'
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
        return dict(row) if row else None
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

async def get_users_nearby(exclude_user_id, lat, lon, seen_ids=None):
    """Поиск людей в радиусе (delta) с учетом уже просмотренных анкет"""
    # Защита: если локации нет, поиск "рядом" невозможен.
    # Иначе Postgres может упасть на выражениях вида $2 - $4 с "unknown".
    if lat is None or lon is None:
        return None

    delta = 0.08  # Примерно 8-10 км
    if seen_ids is None:
        seen_ids = []

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            '''
            SELECT user_id, name, age, drink, photo_id, about, lat, lon 
            FROM users 
            WHERE user_id != $1 
              AND user_id != ALL($5::bigint[])
              AND lat BETWEEN ($2::double precision - $4::double precision)
                          AND ($2::double precision + $4::double precision)
              AND lon BETWEEN ($3::double precision - $4::double precision)
                          AND ($3::double precision + $4::double precision)
            ORDER BY RANDOM() 
            LIMIT 1
        ''',
            exclude_user_id,
            lat,
            lon,
            delta,
            seen_ids,
        )
        return row
    finally:
        await conn.close()


async def get_all_users(exclude_user_id, seen_ids=None):
    """Поиск 'Везде' с учетом уже просмотренных анкет"""
    if seen_ids is None:
        seen_ids = []

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            '''
            SELECT user_id, name, age, drink, photo_id, about, lat, lon 
            FROM users 
            WHERE user_id != $1 
              AND user_id != ALL($2::bigint[])
            ORDER BY RANDOM() 
            LIMIT 1
        ''',
            exclude_user_id,
            seen_ids,
        )
        return row
    finally:
        await conn.close()

async def save_user(user_id, data):
    """Сохраняет профиль (включая координаты) со статусом 'pending' для модерации"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            '''
            INSERT INTO users (user_id, name, age, drink, about, photo_id, lat, lon, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
            ON CONFLICT (user_id) DO UPDATE 
            SET name = EXCLUDED.name, age = EXCLUDED.age, drink = EXCLUDED.drink, 
                about = EXCLUDED.about, photo_id = EXCLUDED.photo_id,
                lat = EXCLUDED.lat, lon = EXCLUDED.lon, status = EXCLUDED.status
        ''',
            user_id,
            data.get('name'),
            data.get('age'),
            data.get('drink'),
            data.get('about'),
            data.get('photo_id'),
            data.get('lat'),
            data.get('lon'),
        )
    finally:
        await conn.close()

async def update_user_status(user_id: int, status: str) -> None:
    """Обновляет статус модерации пользователя (pending/approved/rejected)"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            'UPDATE users SET status = $1 WHERE user_id = $2',
            status,
            user_id
        )
    finally:
        await conn.close()

async def update_location(user_id: int, lat: float, lon: float) -> None:
    """Обновляет только координаты пользователя"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            '''
            UPDATE users
            SET lat = $2, lon = $3
            WHERE user_id = $1
        ''',
            user_id,
            lat,
            lon,
        )
    finally:
        await conn.close()


async def add_like(liker_id, liked_id):
    """Записывает лайк и проверяет на взаимность"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            'CREATE TABLE IF NOT EXISTS likes (liker_id BIGINT, liked_id BIGINT)'
        )
        await conn.execute(
            'INSERT INTO likes (liker_id, liked_id) VALUES ($1, $2)',
            liker_id,
            liked_id,
        )

        match = await conn.fetchval(
            'SELECT 1 FROM likes WHERE liker_id = $1 AND liked_id = $2',
            liked_id,
            liker_id,
        )
        return match is not None
    finally:
        await conn.close()


async def delete_user(user_id):
    """Полностью удаляет анкету пользователя и связанные лайки"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            'DELETE FROM likes WHERE liker_id = $1 OR liked_id = $1', user_id
        )
        await conn.execute('DELETE FROM users WHERE user_id = $1', user_id)
    finally:
        await conn.close()


async def get_all_user_ids():
    """Получает список всех user_id из таблицы users"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch('SELECT user_id FROM users')
        return [row['user_id'] for row in rows]
    finally:
        await conn.close()


async def approve_all_users():
    """Активирует все анкеты (устанавливает статус 'approved' для всех пользователей)"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.execute(
            "UPDATE users SET status = 'approved' WHERE status != 'approved'"
        )
        return result.split()[-1]  # Возвращает количество обновленных строк
    finally:
        await conn.close()