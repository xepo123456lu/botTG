import aiosqlite

DB_NAME = "users_v1.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                age TEXT,
                drink TEXT,
                photo_id TEXT,
                about TEXT,
                lat REAL,
                lon REAL
            )
        ''')
        await db.commit()

async def save_user(user_id, data):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, name, age, drink, photo_id, about)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, 
            data.get('name'), 
            data.get('age'), 
            data.get('drink'), 
            data.get('photo_id'), 
            data.get('about')
        ))
        await db.commit()

async def get_random_user(exclude_user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT name, age, drink, photo_id, about FROM users 
            WHERE user_id != ? 
            ORDER BY RANDOM() LIMIT 1
        ''', (exclude_user_id,)) as cursor:
            return await cursor.fetchone()
async def get_nearest_user(exclude_user_id, lat, lon):
    async with aiosqlite.connect(DB_NAME) as db:
        # Ищем тех, кто находится в радиусе примерно 50 км
        async with db.execute('''
            SELECT name, age, drink, photo_id, about FROM users 
            WHERE user_id != ? 
            AND lat BETWEEN ? - 0.5 AND ? + 0.5
            AND lon BETWEEN ? - 0.5 AND ? + 0.5
            ORDER BY RANDOM() LIMIT 1
        ''', (exclude_user_id, lat, lat, lon, lon)) as cursor:
            return await cursor.fetchone()

async def user_exists(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None
async def get_users_nearby(exclude_user_id, lat, lon):
    async with aiosqlite.connect(DB_NAME) as db:
        # 0.05 градуса — это примерно 5-7 км. 
        # Это создаст "квадрат поиска" вокруг пользователя
        delta = 0.08 
        
        async with db.execute('''
            SELECT user_id, name, age, drink, photo_id, about, lat, lon 
            FROM users 
            WHERE user_id != ? 
            AND lat BETWEEN ? - ? AND ? + ?
            AND lon BETWEEN ? - ? AND ? + ?
            ORDER BY RANDOM() LIMIT 1
        ''', (exclude_user_id, lat, delta, lat, delta, lon, delta, lon, delta)) as cursor:
            return await cursor.fetchone()
async def add_like(liker_id, liked_id):
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute(
            "INSERT OR IGNORE INTO likes (liker_id, liked_id) VALUES (?, ?)",
            (liker_id, liked_id)
        )
        await db.commit()