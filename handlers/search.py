from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite

# Импортируем нужные функции из других твоих файлов
from database import get_users_nearby, add_like
from keyboards import get_search_kb # Эту функцию мы создали в keyboards.py

router = Router()

@router.message(F.text == "Найти подругу 🔍")
async def find_friend(message: types.Message):
    await message.answer("Ищу подруг рядом с тобой...")
    
    # Берем координаты пользователя из базы
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT lat, lon FROM users WHERE user_id = ?", (user_id,)) as cursor:
            me = await cursor.fetchone()
    
    if not me or me[0] is None:
        await message.answer("Чтобы искать подруг рядом, мне нужны твои координаты. Пройди регистрацию заново.")
        return

    # Ищем кого-то в радиусе (delta)
    friend = await get_users_nearby(user_id, me[0], me[1])

    if friend:
        f_id, f_name, f_age, f_drink, f_photo, f_about, f_lat, f_lon = friend
        
        caption = (f"✨ Найдена подруга рядом!\n\n"
                   f"👤 <b>Имя:</b> {f_name}, {f_age}\n"
                   f"🥂 <b>Куда сходим:</b> {f_drink}\n"
                   f"📝 <b>О себе:</b> {f_about if f_about else 'Пока пусто'}")
        
        # Используем инлайн-кнопки (Лайк / Дальше)
        await message.answer_photo(
            photo=f_photo, 
            caption=caption, 
            reply_markup=get_search_kb(f_id), # Передаем ID найденной девушки для лайка
            parse_mode="HTML"
        )
    else:
        await message.answer("Поблизости пока никого нет... 😔\nПопробуй зайти позже!")

# Обработка кнопки Лайк
@router.callback_query(F.data.startswith("like_"))
async def handle_like(callback: types.CallbackQuery, bot):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    is_match = await add_like(from_id, to_id)
    
    if is_match:
        await callback.message.answer("🎉 Это взаимно! Напиши ей: <a href='tg://user?id={to_id}'>СЮДА</a>", parse_mode="HTML")
        await bot.send_message(to_id, f"🌟 У тебя новый мэтч! Тебе поставили лайк: <a href='tg://user?id={from_id}'>ОТКРЫТЬ ЧАТ</a>", parse_mode="HTML")
    else:
        await callback.answer("Лайк отправлен! 😉")
        await find_friend(callback.message)

# Обработка кнопки Дальше
@router.callback_query(F.data == "next_search")
async def handle_next(callback: types.CallbackQuery):
    await callback.message.delete()
    await find_friend(callback.message)