from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_users_nearby, get_all_users, add_like, get_user
from keyboards import get_search_kb, get_location_choice_keyboard, remove_keyboard

router = Router()


class SearchState(StatesGroup):
    choosing_mode = State()
    viewing_profiles = State()


@router.message(F.text == "Найти подругу 🔍")
async def start_search(message: types.Message, state: FSMContext):
    """
    Обработка кнопки меню "Найти подругу 🔍":
    - убираем старую клавиатуру
    - проверяем, есть ли координаты
    - спрашиваем режим поиска
    """
    await remove_keyboard(message, "Готовлю поиск подруг...")

    user_id = message.from_user.id
    me = await get_user(user_id)

    if not me or me.get("lat") is None or me.get("lon") is None:
        await message.answer(
            "Чтобы искать подруг, мне нужно знать, где ты. "
            "Отправь свою локацию при заполнении анкеты."
        )
        return

    await state.update_data(my_lat=me.get("lat"), my_lon=me.get("lon"))

    await message.answer(
        "Как будем искать?", reply_markup=get_location_choice_keyboard()
    )
    await state.set_state(SearchState.choosing_mode)


@router.callback_query(
    F.data.in_(["search_near", "search_all"]), SearchState.choosing_mode
)
async def process_mode_choice(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(search_mode=callback.data)
    await callback.message.delete()
    await show_next_profile(callback.message, state)


async def show_next_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.chat.id

    mode = data.get("search_mode")
    lat = data.get("my_lat")
    lon = data.get("my_lon")

    friend = None
    if mode == "search_near":
        friend = await get_users_nearby(user_id, lat, lon)
    else:
        friend = await get_all_users(user_id)

    if friend:
        f_id, f_name, f_age, f_drink, f_photo, f_about, f_lat, f_lon = friend

        dist_text = (
            "Рядом с тобой!" if mode == "search_near" else "🌍 Из любой точки"
        )
        caption = (
            f"✨ {dist_text}\n\n"
            f"👤 <b>Имя:</b> {f_name}, {f_age}\n"
            f"🥂 <b>Куда сходим:</b> {f_drink}\n"
            f"📝 <b>О себе:</b> {f_about or 'Пока пусто'}"
        )

        await message.answer_photo(
            photo=f_photo,
            caption=caption,
            reply_markup=get_search_kb(f_id),
            parse_mode="HTML",
        )
        await state.set_state(SearchState.viewing_profiles)
    else:
        await message.answer(
            "К сожалению, анкет больше нет... 😔\n"
            "Попробуй сменить режим поиска позже!"
        )
        await state.clear()


@router.callback_query(F.data.startswith("like_"))
async def handle_like(callback: types.CallbackQuery, state: FSMContext, bot):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id

    await callback.message.edit_reply_markup(reply_markup=None)
    is_match = await add_like(from_id, to_id)

    if is_match:
        await callback.message.answer(
            f"🎉 Это взаимно! Напиши ей: "
            f"<a href='tg://user?id={to_id}'>СЮДА</a>",
            parse_mode="HTML",
        )
        await bot.send_message(
            to_id,
            "🌟 У тебя новый мэтч! Тебе поставили лайк: "
            f"<a href='tg://user?id={from_id}'>ОТКРЫТЬ ЧАТ</a>",
            parse_mode="HTML",
        )
    else:
        await callback.answer("Лайк отправлен! 😉")

    await show_next_profile(callback.message, state)


@router.callback_query(F.data == "next_search")
async def handle_next(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await show_next_profile(callback.message, state)