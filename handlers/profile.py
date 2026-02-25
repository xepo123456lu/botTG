from aiogram import Router, F, types
import aiosqlite

router = Router()

# В файле handlers/profile.py
@router.message(F.text == "Моя анкета 👤")
async def my_profile(message: types.Message):
    await message.answer("Вот твоя анкета:")
    # ... код вывода анкеты
    
    user_id = message.from_user.id   # Подключаемся к базе, чтобы забрать свои данные
    async with aiosqlite.connect('users_v1.db') as db:
        async with db.execute(
            "SELECT name, age, drink, photo_id, about FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
    
    if user:
        name, age, drink, photo_id, about = user
        
        # Формируем текст анкеты
        caption = (
            f"<b>Твоя анкета так выглядит для других:</b>\n\n"
            f"👤 <b>Имя:</b> {name}, {age}\n"
            f"🥂 <b>Любимый напиток:</b> {drink}\n"
            f"📝 <b>О себе:</b> {about if about else 'Не заполнено'}\n\n"
            f"<i>Хочешь что-то изменить? Просто нажми /start и пройди регистрацию заново.</i>"
        )
        
        # Отправляем фото с описанием
        if photo_id:
            await message.answer_photo(photo=photo_id, caption=caption, parse_mode="HTML")
        else:
            await message.answer(caption, parse_mode="HTML")
    else:
        await message.answer("Странно, но я не нашел твою анкету. Давай заполним её? Нажми /start")