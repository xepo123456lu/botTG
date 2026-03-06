from aiogram import Router, F, types
from database import get_user
from keyboards import show_profile

router = Router()

@router.message(F.text == "Моя анкета 👤")
async def my_profile(message: types.Message):
    user_id = message.from_user.id

    user = await get_user(user_id)

    if not user:
        await message.answer(
            "Странно, но я не нашёл твою анкету. Давай заполним её? Нажми /start"
        )
        return

    # asyncpg возвращает Record, обращаемся как к dict-подобному объекту
    name = user.get("name", "Не указано")
    age = user.get("age", "Не указан")
    drink = user.get("drink", "Кофе")
    about = user.get("about", "Не заполнено")
    photo_id = user.get("photo_id")

    caption = (
        "<b>Твоя анкета так выглядит для других:</b>\n\n"
        f" <b>Имя:</b> {name}, {age}\n"
        f" <b>Настроение:</b> {drink}\n"
        f" <b>О себе:</b> {about}\n\n"
        "<i>Хочешь что-то изменить? Просто нажми /start и пройди регистрацию заново.</i>"
    )

    await show_profile(message, caption=caption, photo_id=photo_id)