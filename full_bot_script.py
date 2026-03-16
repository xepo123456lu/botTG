import asyncio
import os

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


#
# Полный минимальный пример структуры кнопок:
# - Под анкетой (сообщение с фото): Inline -> "💖 Лайк" и "Дальше ➡️"
# - Внизу (главное меню): Reply Keyboard -> "Редактировать анкету ✏️" и "Удалить анкету 🗑"
#   (плюс "Найти подругу 🔍" и "Моя анкета 👤" как в вашем проекте)
#


def main_menu_kb() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Найти подругу 🌖")],
            [types.KeyboardButton(text="Моя анкета 🌘")],
            [types.KeyboardButton(text="Редактировать анкету 🌑")],
            [types.KeyboardButton(text="Удалить анкету 🌒")],
            [types.KeyboardButton(text="Пожаловаться 🌓")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие...",
    )


def profile_inline_kb(target_id: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Лайк ♥️", callback_data=f"like_{target_id}"
                ),
                types.InlineKeyboardButton(text="Дальше 🥀", callback_data="next"),
            ]
        ]
    )


router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Главное меню. (Заглушка)\n\n"
        "Кнопки «Редактировать/Удалить» находятся внизу в Reply-меню.\n"
        "Под анкетой будут только «Лайк/Дальше» (inline).",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "Найти подругу 🌖")
async def start_search(message: types.Message) -> None:
    # Заглушка анкеты, как у вас на скринах (сообщение с фото + inline кнопки)
    caption = (
        " Из любой точки\n\n"
        " <b>Имя:</b> Юля, 29\n"
        " <b>Куда сходим:</b> None\n"
        " <b>О себе:</b> грустное"
    )
    await message.answer_photo(
        photo="https://placekitten.com/800/800",
        caption=caption,
        parse_mode="HTML",
        reply_markup=profile_inline_kb(target_id=123),
    )


@router.callback_query(F.data.startswith("like_"))
async def on_like(callback: types.CallbackQuery) -> None:
    await callback.answer("Лайк! (заглушка)")
    # Чтобы “под сообщением” не оставались старые кнопки — можно снять разметку:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data == "next")
async def on_next(callback: types.CallbackQuery) -> None:
    await callback.answer()
    # Обычно: удалить текущую карточку и показать следующую
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Следующая анкета… (заглушка)", reply_markup=main_menu_kb())


@router.message(F.text == "Моя анкета 🌘")
async def my_profile(message: types.Message) -> None:
    await message.answer("Твоя анкета. (заглушка)", reply_markup=main_menu_kb())


@router.message(F.text == "Редактировать анкету 🌑")
async def edit_profile(message: types.Message, state: FSMContext) -> None:
    # Заглушка — тут запускайте ваш сценарий редактирования/регистрации
    await state.clear()
    await message.answer("Редактирование анкеты… (заглушка)", reply_markup=main_menu_kb())


@router.message(F.text == "Удалить анкету 🌒")
async def delete_profile(message: types.Message) -> None:
    # Заглушка — тут удаляйте из БД
    await message.answer("Анкета удалена. (заглушка)", reply_markup=main_menu_kb())


@router.message(F.text == "Пожаловаться 🌓")
async def complaint_menu(message: types.Message) -> None:
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
    await message.answer("Напиши модератору, что случилось.", reply_markup=kb)


async def main() -> None:
    token = os.getenv("API_TOKEN") or os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Set API_TOKEN (or BOT_TOKEN) env var")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

