from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    Message,
)

# ---------- ОСНОВНЫЕ КЛАВИАТУРЫ ----------

# ГЛАВНОЕ МЕНЮ (Reply Keyboard, заменяет стандартную клавиатуру)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Найти подругу 🌖")],
        [KeyboardButton(text="Моя анкета 🌘")],
        [KeyboardButton(text="Редактировать анкету 🌑")],
        [KeyboardButton(text="Удалить анкету 🌒")],
        [KeyboardButton(text="Пожаловаться 🌓")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие...",
)

# Клавиатура поиска (Лайк / Пропустить / В главное меню)
search_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Лайк ♥️"), KeyboardButton(text="Пропустить 🥀")],
        [KeyboardButton(text="В главное меню 🧺")],
    ],
    resize_keyboard=True,
)

# Клавиатура геолокации
kb_geo = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поделиться локацией 🚏", request_location=True)],
        [KeyboardButton(text="Пропустить")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Клавиатура с кнопкой "Пропустить"
kb_skip = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Клавиатура с кнопкой "Отмена"
kb_cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена 🥀")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# ---------- ИНЛАЙН-КЛАВИАТУРЫ ----------

# Инлайн-кнопки для поиска (под фото анкеты)
def get_search_kb(target_id: int) -> InlineKeyboardMarkup:
    """
    Кнопки под конкретной анкетой:
    - Лайк
    - Дальше
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♥️", callback_data=f"like_{target_id}"
                ),
                InlineKeyboardButton(
                    text="Дальше 🥀", callback_data="next_search"
                ),
            ],
        ]
    )
    return keyboard


def get_location_choice_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора режима поиска: Рядом или Везде.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚏 Рядом со мной", callback_data="search_near"
                ),
                InlineKeyboardButton(
                    text="Везде", callback_data="search_all"
                ),
            ]
        ]
    )
    return keyboard


# ---------- СЕРВИСНЫЕ ФУНКЦИИ ----------

async def remove_keyboard(message: Message, text: str | None = None) -> None:
    """
    Полностью убирает текущую клавиатуру (ReplyKeyboard).
    Можно передать текст, который отправится вместе с удалением.
    """
    await message.answer(
        text or "Клавиатура убрана.",
        reply_markup=ReplyKeyboardRemove(),
    )


async def show_main_menu(message: Message, text: str | None = None) -> None:
    """
    Показывает главное меню и предварительно убирает старую клавиатуру.
    """
    await remove_keyboard(message, text or "Главное меню. Выбери действие:")
    await message.answer("Выбери действие:", reply_markup=main_kb)


async def show_profile(
    message: Message,
    caption: str,
    photo_id: str | None = None,
) -> None:
    """
    Показывает анкету пользователя и возвращает главное меню.
    """
    await remove_keyboard(message)

    if photo_id:
        await message.answer_photo(
            photo=photo_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=main_kb,
        )
    else:
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=main_kb,
        )