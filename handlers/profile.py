from aiogram import Router, F, types
from aiogram.types import Message
from database import get_user, delete_user
from keyboards import main_kb  # Убедись, что main_kb создана в keyboards.py

router = Router()


@router.message(F.text == "Моя анкета 👤")
async def show_my_profile(message: Message):
    user_id = message.from_user.id
    user_data = await get_user(user_id)

    if user_data:
        # Формируем текст анкеты.
        # Если каких-то данных нет, выводим "Не указано" вместо None
        text = (
            f"<b>Твоя анкета:</b>\n\n"
            f"Имя: {user_data['name']}\n"
            f"Возраст: {user_data['age']}\n"
            f"Любимый напиток: {user_data['drink'] or 'Не указано'}\n"
            f"О себе: {user_data['about'] or 'Не указано'}"
        )

        if user_data['photo_id']:
            await message.answer_photo(
                photo=user_data['photo_id'],
                caption=text,
                reply_markup=main_kb,
            )
        else:
            await message.answer(text, reply_markup=main_kb)
    else:
        await message.answer(
            "Твоя анкета не найдена. Нажми /start, чтобы зарегистрироваться.",
            reply_markup=main_kb,
        )


@router.message(F.text == "Удалить анкету 🗑")
async def delete_my_profile(message: Message):
    user_id = message.from_user.id
    await delete_user(user_id)
    await message.answer(
        "Твоя анкета удалена. Если захочешь, можешь создать новую командой /start.",
        reply_markup=main_kb,
    )