from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ГЛАВНОЕ МЕНЮ (после регистрации)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Найти подругу 🔍")],
        [KeyboardButton(text="Моя анкета 👤")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие..."
)

# КНОПКА ОТПРАВКИ ГЕОПОЗИЦИИ
kb_geo = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поделиться локацией 📍", request_location=True)],
        [KeyboardButton(text="/skip")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# КНОПКА ПРОПУСКА (для необязательных полей)
kb_skip = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/skip")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# ИНЛАЙН-КНОПКИ ДЛЯ ПОИСКА (под фото анкеты)
def get_search_kb(target_id):
    """
    Функция создает кнопки специально под конкретную анкету.
    target_id — это ID пользователя, которого мы сейчас смотрим.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💖 Лайк", callback_data=f"like_{target_id}"),
            InlineKeyboardButton(text="Дальше ➡️", callback_data="next_search")
        ]
    ])
    return keyboard

# КНОПКА ПОДТВЕРЖДЕНИЯ (если захочешь сделать превью анкеты)
kb_confirm = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Всё верно ✅")],
        [KeyboardButton(text="Заполнить заново 🔄")]
    ],
    resize_keyboard=True
)