from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
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


@router.message(F.text == "Редактировать анкету ✏️")
async def edit_my_profile(message: Message, state: FSMContext):
    """
    Перенесённая в главное меню функция редактирования анкеты.
    Заглушка: переиспользуем сценарий регистрации (/start).
    """
    from handlers.registration import cmd_start

    await cmd_start(message, state)


@router.message(F.text == "Удалить анкету 🗑")
async def delete_my_profile(message: Message):
    user_id = message.from_user.id
    await delete_user(user_id)
    await message.answer(
        "Твоя анкета удалена. Если захочешь, можешь создать новую командой /start.",
        reply_markup=main_kb,
    )


@router.message(F.text == "Пожаловаться 🚫")
async def complaint_menu(message: Message) -> None:
    """
    Кнопка жалобы в главном нижнем меню.
    Reply-кнопка не может сама открыть чат, поэтому отправляем ссылку/кнопку.
    """
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Написать модератору",
                    url="https://t.me/ffffrttee",
                )
            ]
        ]
    )
    await message.answer(
        "Опиши проблему модератору в личных сообщениях.",
        reply_markup=kb,
    )