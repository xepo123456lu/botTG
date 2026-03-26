from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

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


# ⚠️ ВРЕМЕННЫЙ ОБРАБОТЧИК - УДАЛИТЬ ПОСЛЕ АКТИВАЦИИ ⚠️
@router.message(Command("activate_all"))
async def cmd_activate_all(message: types.Message) -> None:
    """
    Команда /activate_all - активирует все анкеты (устанавливает статус 'approved')
    ⚠️ УДАЛИТЬ ЭТОТ ОБРАБОТЧИК ПОСЛЕ ИСПОЛЬЗОВАНИЯ ⚠️
    """
    # Проверка: только админ может активировать анкеты
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет прав на эту команду.")
        return

    from database import approve_all_users

    try:
        updated_count = await approve_all_users()
        await message.answer(
            f"✅ <b>Все анкеты активированы!</b>\n\n"
            f"Обновлено анкет: <code>{updated_count}</code>\n\n"
            f"Теперь все пользователи могут искать подруг! 🌖\n\n"
            f"⚠️ <b>ВАЖНО:</b> Удалите этот обработчик /activate_all из common.py!"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при активации: {e}")
        print(f"Ошибка активации анкет: {e}")

