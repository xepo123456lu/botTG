from aiogram import Router, F, types
from aiogram.filters import Command
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_users_nearby, get_all_users, add_like, get_user
from keyboards import get_search_kb, get_location_choice_keyboard, remove_keyboard
from viewed_storage import get_viewed_ids, mark_viewed

router = Router()


class SearchState(StatesGroup):
    choosing_mode = State()
    viewing_profiles = State()
    writing_message = State()
    waiting_location = State()


@router.message(Command("search"))
@router.message(F.text == "Найти подругу 🌖")
async def start_search(message: types.Message, state: FSMContext):
    """
    Обработка кнопки меню "Найти подругу 🌖":
    - убираем старую клавиатуру
    - проверяем статус модерации
    - проверяем, есть ли координаты
    - спрашиваем режим поиска
    """
    await remove_keyboard(message, "Готовлю поиск подруг...")

    user_id = message.from_user.id
    me = await get_user(user_id)

    # Локация нужна только для режима "рядом". Режим "везде" доступен всегда.
    if not me:
        await message.answer("Сначала создай анкету командой /start.")
        return

    # 🔴 ПРОВЕРКА СТАТУСА МОДЕРАЦИИ
    status = me.get("status", "pending")
    
    if status == "pending":
        await message.answer(
            "Твоя анкета ещё находится на модерации. 🕐\n"
            "Мы пришлём уведомление, когда её одобрят! ✨"
        )
        await state.set_state(None)
        return
    
    if status == "rejected":
        await message.answer(
            "К сожалению, твоя анкета не прошла модерацию. ❌\n"
            "Попробуй перезаполнить её в профиле."
        )
        await state.set_state(None)
        return
    
    if status != "approved":
        await message.answer("Ошибка статуса. Свяжись с поддержкой.")
        return

    # ✅ СТАТУС OK - НАЧИНАЕМ ПОИСК
    await state.update_data(
        my_lat=me.get("lat"),
        my_lon=me.get("lon"),
    )

    await message.answer(
        "Как будем искать?", reply_markup=get_location_choice_keyboard()
    )
    await state.set_state(SearchState.choosing_mode)


@router.callback_query(
    F.data.in_(["search_near", "search_all"]), SearchState.choosing_mode
)
async def process_mode_choice(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lat = data.get("my_lat")
    lon = data.get("my_lon")

    if callback.data == "search_near" and (lat is None or lon is None):
        await callback.answer()
        await callback.message.answer(
            "Чтобы искать рядом, пришли свою локацию.\n"
            "Локация нужна только для режима «Рядом» — в режиме «Везде» она не требуется.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [
                        types.KeyboardButton(
                            text="Поделиться локацией 🚏", request_location=True
                        )
                    ],
                    [types.KeyboardButton(text="Пропустить")],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        await state.set_state(SearchState.waiting_location)
        return

    await callback.answer()

    await state.update_data(search_mode=callback.data)
    # Не удаляем сообщение жестко (иногда Telegram не даёт удалить) — просто убираем инлайн-кнопки.
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await show_next_profile(callback.message, state)
    except Exception as e:
        # Чтобы не было "тишины" при падении, показываем сообщение пользователю,
        # а ошибку выводим в логи хостинга.
        print(f"process_mode_choice error: {e!r}")
        await callback.message.answer(
            "Что-то пошло не так при поиске. Попробуй ещё раз командой /search."
        )


@router.message(SearchState.waiting_location)
async def handle_location_for_nearby(
    message: types.Message, state: FSMContext
):
    """
    Запрашиваем локацию только когда пользователь выбрал поиск "рядом".
    """
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude

        from database import update_location

        await update_location(message.from_user.id, lat, lon)
        await state.update_data(my_lat=lat, my_lon=lon)

        await message.answer(
            "Локация получена. Ищу анкеты рядом…",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.update_data(search_mode="search_near")
        await state.set_state(SearchState.viewing_profiles)
        await show_next_profile(message, state)
        return

    if message.text == "Пропустить":
        await message.answer(
            "Ок, тогда выбирай режим «Везде».",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.set_state(SearchState.choosing_mode)
        await message.answer(
            "Как будем искать?",
            reply_markup=get_location_choice_keyboard(),
        )
        return

    await message.answer("Пришли локацию кнопкой ниже или нажми «Пропустить».")


async def show_next_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.chat.id

    mode = data.get("search_mode")
    lat = data.get("my_lat")
    lon = data.get("my_lon")
    seen_ids = await get_viewed_ids(user_id)

    if mode == "search_near" and (lat is None or lon is None):
        await message.answer(
            "Для поиска рядом нужна локация. Выбери «Рядом» ещё раз и пришли локацию."
        )
        await state.set_state(SearchState.choosing_mode)
        await message.answer(
            "Как будем искать?", reply_markup=get_location_choice_keyboard()
        )
        return

    friend = None
    if mode == "search_near":
        friend = await get_users_nearby(user_id, lat, lon, seen_ids)
    else:
        friend = await get_all_users(user_id, seen_ids)

    if friend:
        f_id, f_name, f_age, f_city, f_photo, f_about, f_lat, f_lon = friend

        dist_text = (
            "Рядом с тобой!" if mode == "search_near" else "🌍 Из любой точки"
        )
        caption = (
            f"✨ {dist_text}\n\n"
            f" <b>Имя:</b> {f_name}, {f_age}\n"
            f"Город: {f_city or 'Не указано'}\n"
            f"<b>О себе:</b> {f_about or 'Пока пусто'}"
        )

        await message.answer_photo(
            photo=f_photo,
            caption=caption,
            reply_markup=get_search_kb(f_id),
            parse_mode="HTML",
        )
        await mark_viewed(user_id, f_id)
        await state.set_state(SearchState.viewing_profiles)
    else:
        await message.answer(
            "Пока рядом нет анкет.\n"
            "Измени критерии поиска или зайди позже."
            if mode == "search_near"
            else
            "К сожалению, анкет больше нет... 🥀\n"
            "Попробуй сменить режим поиска позже!"
        )
        await state.clear()


@router.callback_query(F.data.startswith("like_"))
async def handle_like(callback: types.CallbackQuery, state: FSMContext, bot):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id

    await callback.message.edit_reply_markup(reply_markup=None)
    is_match = await add_like(from_id, to_id)

    # Достаём анкету лайкнувшего (юзера A), чтобы показать её юзеру B
    me = await get_user(from_id)

    # Кнопка для открытия чата с инициатором лайка
    kb_open_chat_with_a = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Открыть чат",
                    url=f"tg://user?id={from_id}",
                )
            ]
        ]
    )

    if me and me.get("photo_id"):
        # Формируем карточку юзера A, чтобы отправить её юзеру B
        caption_for_b = (
            f" Тебе поставили ♥️!\n\n"
            f" <b>Имя:</b> {me.get('name')}, {me.get('age')}\n"
            f"Город: {me.get('drink') or 'Не указано'}\n"
            f"<b>О себе:</b> {me.get('about') or 'Пока пусто'}"
        )
        await bot.send_photo(
            chat_id=to_id,
            photo=me.get("photo_id"),
            caption=caption_for_b,
            reply_markup=kb_open_chat_with_a,
            parse_mode="HTML",
        )
    else:
        # Если по какой-то причине нет анкеты/фото, шлём просто текст
        await bot.send_message(
            to_id,
            "👀 Тебе поставили лайк! Открой чат, чтобы познакомиться.",
            reply_markup=kb_open_chat_with_a,
        )

    if is_match:
        # Сообщение отправителю (юзеру A) при взаимном лайке
        kb_to_friend = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Написать ей",
                        url=f"tg://user?id={to_id}",
                    )
                ]
            ]
        )
        await callback.message.answer(
            "Это взаимно! Напиши ей:",
            reply_markup=kb_to_friend,
        )
    else:
        await callback.answer(
            "Твой лайк отправлен. 🦦"
        )

    # Небольшая пауза перед показом следующей анкеты
    await asyncio.sleep(5)
    await show_next_profile(callback.message, state)


@router.callback_query(F.data.startswith("complaint_"))
async def handle_complaint(callback: types.CallbackQuery, bot):
    """
    Пользователь жалуется на показанную анкету.
    Текст жалобы уходит в личку админа @ffffrttee.
    """
    target_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id
    from_username = callback.from_user.username

    admin_chat_id = "@ffffrttee"

    text = (
        "🌖 Новая жалоба на анкету\n\n"
        f"От пользователя: {from_id}"
        f"{f' (@{from_username})' if from_username else ''}\n"
        f"На пользователя: {target_id}\n\n"
        f"Открыть чат с отправителем: tg://user?id={from_id}\n"
        f"Открыть чат с анкетой: tg://user?id={target_id}"
    )

    await bot.send_message(admin_chat_id, text)
    await callback.answer("Жалоба отправлена модератору.", show_alert=True)


@router.callback_query(F.data == "next_search")
async def handle_next(callback: types.CallbackQuery, state: FSMContext):
    await show_next_profile(callback.message, state)


@router.callback_query(F.data.startswith("msg_"))
async def handle_start_message(callback: types.CallbackQuery, state: FSMContext):
    """
    Пользователь хочет отправить текстовое сообщение автору анкеты.
    """
    to_id = int(callback.data.split("_")[1])
    await state.update_data(current_message_recipient=to_id)
    await callback.answer()
    await callback.message.answer(
        "Напиши сообщение для неё (только текст, без фото)."
    )
    await state.set_state(SearchState.writing_message)


@router.message(SearchState.writing_message)
async def handle_send_message(
    message: types.Message, state: FSMContext, bot: types.Bot
):
    data = await state.get_data()
    to_id = data.get("current_message_recipient")
    sender_id = message.from_user.id

    if not to_id:
        await message.answer(
            "Не удалось определить получателя сообщения. Попробуй выбрать анкету ещё раз."
        )
        await state.set_state(SearchState.viewing_profiles)
        return

    # --- НОВЫЙ БЛОК: достаем анкету отправителя (тебя) ---
    me = await get_user(sender_id)
    
    kb_open_chat_with_sender = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Открыть чат",
                    url=f"tg://user?id={sender_id}",
                )
            ]
        ]
    )

    if me and me.get("photo_id"):
        # Если анкета есть, шлем ФОТО + ТЕКСТ сообщения
        caption_text = (
            f"💌 <b>Новое сообщение для тебя:</b>\n\n"
            f"<i>\"{message.text}\"</i>\n\n"
            f"🏙 Город: {me.get('drink') or 'Не указано'}\n"
            f"👤 От: {me.get('name')}, {me.get('age')}"
        )
        await bot.send_photo(
            chat_id=to_id,
            photo=me.get("photo_id"),
            caption=caption_text,
            reply_markup=kb_open_chat_with_sender,
            parse_mode="HTML",
        )
    else:
        # Если анкеты вдруг нет, шлем как раньше просто текст
        text = (
            "Тебе новое сообщение от участницы:\n\n"
            f"{message.text}"
        )
        await bot.send_message(
            chat_id=to_id,
            text=text,
            reply_markup=kb_open_chat_with_sender,
        )
    # --- КОНЕЦ НОВОГО БЛОКА ---

    await message.answer("Сообщение отправлено. ♥️")
    await state.set_state(SearchState.viewing_profiles)