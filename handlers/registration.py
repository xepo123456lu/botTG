from keyboards import kb_skip, main_kb, get_search_kb, show_main_menu
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, Message, InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем наши функции из новой database.py
from database import user_exists, save_user

router = Router()

# Определение состояний анкеты
class Form(StatesGroup):
    name = State()
    age = State()
    about = State()
    city = State()
    photo = State()
    saving = State()

# Твой ID фото для приветствия
WELCOME_PHOTO = 'AgACAgQAAxkBAAMDaZyK0R9Xv1XaqjA_H8LLmSoAAbxWAAJrDWsbMYXhUDtX42SBVCcvAQADAgADeAADOgQ' 

# --- КОМАНДА /START ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # ВАЖНО: Всегда сбрасываем состояние
    await state.clear()
    
    # Убираем клавиатуру, если она была и сразу начинаем регистрацию
    await message.answer("Запускаем регистрацию анкеты.", reply_markup=ReplyKeyboardRemove())

    # Начинаем регистрацию заново
    await message.answer_photo(
        photo=WELCOME_PHOTO,
        caption="Давай создадим твою анкету, чтобы подруги могли тебя найти.\n\nКак тебя зовут?"
    )
    await state.set_state(Form.name)


# --- ПРОЦЕСС РЕГИСТРАЦИИ ---

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    # Убираем проверку на /skip, просто берем текст
    await state.update_data(name=message.text)
    await message.answer(f"Приятно познакомиться, {message.text}! Сколько тебе лет?")
    await state.set_state(Form.age)
    await state.set_state(Form.age)

from aiogram.types import ReplyKeyboardRemove

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    # Проверяем, что ввели число
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст цифрами (например, 20).")
        return

    age = int(message.text)
    if age < 18 or age > 100:
        await message.answer("Возраст должен быть реальным (от 18 лет).")
        return

    await state.update_data(age=age)
    
    # К напитку уже можно прикрепить кнопку пропуска, если он необязателен
    await message.answer(
        "Раскажи о себе и с кем бы ты хотела познакомиться? Например, расскажи где работаешь, с кем живешь и какое твое любимое хобби. Ты ищешь подругу что бы вместе работать в кафе, обсуждать книги, переписываться или свой вариант", 
        reply_markup=kb_skip 
    )
    
    await state.set_state(Form.about)

@router.message(Form.about)
async def process_about(message: Message, state: FSMContext):
    about = (
        message.text
        if message.text != "Пропустить"
        else "Пока ничего не рассказала"
    )
    await state.update_data(about=about)

    # Вопрос про город (можно пропустить)
    await message.answer(
        "Где ты живешь? (Можно пропустить)",
        reply_markup=kb_skip,
    )
    await state.set_state(Form.city)


@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    city = None if message.text == "Пропустить" else message.text

    # Сохраняем город в поле drink (колонка БД уже есть)
    await state.update_data(drink=city)

    # Локацию НЕ спрашиваем при создании анкеты — она понадобится только для поиска "рядом".
    await message.answer(
        "Теперь пришли свое фото. Это обязательно!",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Form.photo)

@router.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    # Ограничение: в анкете только одно фото.
    # Если пользователь отправил "альбом" или пытается прислать второе фото — игнорируем.
    data = await state.get_data()
    if data.get("photo_id"):
        await message.answer("Фото уже получено. В анкете может быть только одно фото.")
        return

    # Блокируем стейт на время сохранения, чтобы при альбоме не было гонки.
    await state.set_state(Form.saving)

    # 1. Берем фото и сохраняем его в состояние
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    # 2. Извлекаем ВСЕ данные, которые мы собрали (имя, возраст, локация и т.д.)
    user_data = await state.get_data()
    user_id = message.from_user.id
    
    # 3. Сохраняем в Supabase (используем твою функцию из database.py)
    # Твоя save_user принимает (user_id, data)
    from database import save_user
    await save_user(user_id, user_data)
    
    # 4. Выводим твой текст и главное меню, убирая старые кнопки
    await message.answer("Красивое фото! ♥️")
    await show_main_menu(
        message,
        text="Твоя анкета сохранена. Теперь ты можешь искать подруг!",
    )

    # После сохранения анкеты сразу предлагаем выбор режима поиска
    from keyboards import get_location_choice_keyboard
    from handlers.search import SearchState

    await state.update_data(
        my_lat=user_data.get("lat"),
        my_lon=user_data.get("lon"),
        seen_ids=[],
    )
    await message.answer(
        "Как будем искать?",
        reply_markup=get_location_choice_keyboard(),
    )
    await state.set_state(SearchState.choosing_mode)

# Если пользователь продолжает слать фото/текст пока сохраняем анкету
@router.message(Form.saving)
async def process_saving(message: Message) -> None:
    await message.answer("Сохраняю анкету… Подожди пару секунд.")

# Дополнительный хендлер для тех, кто пытается пропустить фото или прислать текст
@router.message(Form.photo)
async def process_photo_invalid(message: Message):
    await message.answer("Без фото нельзя! Это обязательно. Пожалуйста, пришли фотографию.")
    
    # --- ФИНАЛЬНЫЙ ШАГ: СОХРАНЕНИЕ В ОБЛАКО ---