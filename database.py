import ssl
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Подключение к облаку
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(
    MONGO_URL,
    tls=True,
    tlsAllowInvalidCertificates=True
)
db = client['bar_bot_db']           # Подключаемся к базе
users_collection = db['users']
likes_collection = db['likes']
async def init_db():
    """Проверка связи с облаком"""
    try:
        await client.admin.command('ping')
        print("Связь с MongoDB установлена! ✅")
    except Exception as e:
        print(f"Ошибка базы: {e}")

async def user_exists(user_id):
    """Проверяет, есть ли пользователь в базе"""
    user = await users_collection.find_one({"user_id": user_id})
    return user is not None

async def save_user(user_id, data):
    """Сохраняет профиль (имя, возраст, фото, локация и т.д.)"""
    # Мы добавляем user_id в сам объект данных для удобства
    data["user_id"] = user_id
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

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