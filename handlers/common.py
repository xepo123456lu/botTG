from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    """
    Обработчик команды /help.
    Показывает краткую инструкцию и кнопку для связи с разработчиком.
    """
    text = (
        "Здесь ты можешь найти подруг для общения и совместных выходов.\n\n"
        "1. Создай анкету командой /start.\n"
        "2. Ищи анкеты через /search.\n"
        "3. Свою анкету можно посмотреть и изменить через /profile и /edit.\n\n"
        "Если что-то работает не так, как ожидалось, напиши разработчику:"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Связаться с разработчиком",
                    url="https://t.me/ffffrttee",
                )
            ]
        ]
    )

    await message.answer(text, reply_markup=kb)

