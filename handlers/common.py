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


# ⚠️ ВРЕМЕННАЯ РАССЫЛКА - УДАЛИТЬ ПОСЛЕ ИСПОЛЬЗОВАНИЯ ⚠️
@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message) -> None:
    """
    Команда /broadcast - отправляет сообщение всем пользователям
    ⚠️ УДАЛИТЬ ЭТОТ ОБРАБОТЧИК ПОСЛЕ РАССЫЛКИ ⚠️
    """
    # Проверка: только админ может отправлять рассылки
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет прав на эту команду.")
        return

    from database import get_all_user_ids
    from aiogram import Bot
    
    bot = Bot(token=os.getenv("API_TOKEN"))
    user_ids = await get_all_user_ids()
    
    if not user_ids:
        await message.answer("Нет пользователей для рассылки.")
        return

    # ⚠️ ТЕКСТ РАССЫЛКИ - УДАЛИТЬ ПОСЛЕ ИСПОЛЬЗОВАНИЯ ⚠️
    broadcast_text = (
        "Дорогая подружка, к сожалению в боте появились люди которые не должны были сюда попасть. "
        "Мне очень грустно , что некоторые не уважают правила сообщества и лезут куда их не звали. "
        "Поэтому Мы вводим обязательную авторизацию для новых пользователей. "
        "Те кто уже зашел в бот мы пока не можем удалить, просто игнонируйте их"
    )
    
    sent_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=broadcast_text)
            sent_count += 1
        except Exception as e:
            print(f"Ошибка при отправке юзеру {user_id}: {e}")
            failed_count += 1

    await message.answer(
        f"✅ Рассылка завершена!\n"
        f"Отправлено: {sent_count}\n"
        f"Ошибок: {failed_count}\n\n"
        f"⚠️ <b>ВАЖНО:</b> Удалите этот обработчик /broadcast из common.py после в файле рассылки!"
    )

