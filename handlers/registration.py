from keyboards import kb_geo, kb_skip, main_kb, get_search_kb
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

# Импортируем наши кнопки и функции базы
from keyboards import kb_skip, kb_geo, main_kb
from database import user_exists, save_user

router = Router()
# Временный обработчик для получения ID фото


# Определение состояний анкеты
class Form(StatesGroup):
    name = State()
    age = State()
    drink = State()
    location = State()
    photo = State()

# Замени на свой реальный file_id после проверки
WELCOME_PHOTO = 'AgACAgQAAxkBAAMDaZyK0R9Xv1XaqjA_H8LLmSoAAbxWAAJrDWsbMYXhUDtX42SBVCcvAQADAgADeAADOgQ' 

# --- КОМАНДА /START ---
@router.message(CommandStart())

async def cmd_start(message: types.Message, state: FSMContext):
    if await user_exists(message.from_user.id):
        await message.answer_photo(
            photo=WELCOME_PHOTO,
            caption="С возвращением в клуб! ✨ Хочешь найти компанию на сегодня?",
            reply_markup=main_kb
        )
    else:
        await message.answer_photo(
            photo=WELCOME_PHOTO,
            caption="Привет, красотка! 👋 Добро пожаловать.\nДавай создадим твою анкету, чтобы подруги могли тебя найти."
        )
        await message.answer("Как тебя зовут? (можно нажать /skip)", reply_markup=kb_skip)
        await state.set_state(Form.name)

# --- ПРОЦЕСС РЕГИСТРАЦИИ ---

@router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text if message.text != "/skip" else message.from_user.first_name
    await state.update_data(name=name)
    await message.answer(f"Приятно познакомиться, {name}! Сколько тебе лет?", reply_markup=kb_skip)
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    age = message.text if message.text != "/skip" else "Секрет"
    await state.update_data(age=age)
    await message.answer("Какой твой любимый напиток? ☕️🍷", reply_markup=kb_skip)
    await state.set_state(Form.drink)

@router.message(Form.drink)
async def process_drink(message: types.Message, state: FSMContext):
    drink = message.text if message.text != "/skip" else "Кофе"
    await state.update_data(drink=drink)
    await message.answer("Где ты обычно бываешь? Поделись локацией, чтобы найти подруг рядом.", reply_markup=kb_geo)
    await state.set_state(Form.location)

@router.message(Form.location)
async def process_location(message: types.Message, state: FSMContext):
    if message.location:
        await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    else:
        await state.update_data(lat=None, lon=None)
    
    await message.answer("И напоследок: пришли свое фото. 📸 Это обязательно!", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.photo)

@router.message(Form.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    data = await state.get_data()
    # Сохраняем в базу данных
    await save_user(message.from_user.id, data)
    
    await message.answer("Ура! Твоя анкета готова. Теперь ты можешь искать подруг рядом! 🥳", reply_markup=main_kb)
    await state.clear()

# Обработка ошибки, если вместо фото прислали текст
@router.message(Form.photo)
async def photo_error(message: types.Message):
    await message.answer("Пожалуйста, пришли именно фото (как картинку), чтобы завершить регистрацию.")