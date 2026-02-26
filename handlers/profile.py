from aiogram import Router, F, types
from database import get_user  # Импортируем функцию из нашего нового database.py
from keyboards import main_kb

router = Router()

@router.message(F.text == "Моя анкета 👤")
async def my_profile(message: types.Message):
    user_id = message.from_user.id
    
    # Запрашиваем данные из облака MongoDB
    user = await get_user(user_id)
    
    if user:
        # Используем .get(), чтобы бот не "упал", если какого-то поля нет в базе
        name = user.get('name', 'Не указано')
        age = user.get('age', 'Не указан')
        drink = user.get('drink', 'Кофе')
        about = user.get('about', 'Не заполнено')
        photo_id = user.get('photo_id')
        
        # Формируем текст анкеты (как в твоем оригинале)
        caption = (
            f"<b>Твоя анкета так выглядит для других:</b>\n\n"
            f"👤 <b>Имя:</b> {name}, {age}\n"
            f"🥂 <b>Любимый напиток:</b> {drink}\n"
            f"📝 <b>О себе:</b> {about}\n\n"
            f"<i>Хочешь что-то изменить? Просто нажми /start и пройди регистрацию заново.</i>"
        )
        
        # Отправляем фото, если оно есть
        if photo_id:
            await message.answer_photo(
                photo=photo_id, 
                caption=caption, 
                parse_mode="HTML",
                reply_markup=main_kb
            )
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=main_kb)
    else:
        await message.answer("Странно, но я не нашел твою анкету. Давай заполним её? Нажми /start")