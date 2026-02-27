from keyboards import kb_geo, kb_skip, main_kb, get_search_kb
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, Message

# Импортируем наши функции из новой database.py
from database import user_exists, save_user

router = Router()

# Определение состояний анкеты
class Form(StatesGroup):
    name = State()
    age = State()
    about = State()
    location = State()
    photo = State()

# Твой ID фото для приветствия
WELCOME_PHOTO = 'AgACAgQAAxkBAAMDaZyK0R9Xv1XaqjA_H8LLmSoAAbxWAAJrDWsbMYXhUDtX42SBVCcvAQADAgADeAADOgQ' 

# --- КОМАНДА /START ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Проверяем в MongoDB, есть ли уже такая красотка в базе
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
async def process_name(message: Message, state: FSMContext):
    # Если пользователь ввел /skip или текст слишком короткий
    if message.text == "/skip":
        await message.answer("Имя — это важно! Пожалуйста, напиши, как тебя зовут.")
        return # Прерываем функцию, стейт остается Form.name

    name = message.text
    await state.update_data(name=name)
    
    # Для возраста оставляем возможность скипа, поэтому передаем kb_skip
    await message.answer(
        f"Приятно познакомиться, {name}! Сколько тебе лет?", 
        reply_markup=kb_skip
    )
    await state.set_state(Form.age)

from aiogram.types import ReplyKeyboardRemove

@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    # Проверяем, является ли ввод числом
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст цифрами (например, 25).")
        return # Останавливаем выполнение, стейт не меняется

    age = int(message.text)

    # Дополнительная проверка на адекватность возраста
    if age < 18 or age > 99:
        await message.answer("Возраст должен быть от 18 до 99 лет. Попробуй еще раз!")
        return

    # Если всё хорошо, сохраняем и идем дальше
    await state.update_data(age=age)
    
    # К напитку уже можно прикрепить кнопку пропуска, если он необязателен
    await message.answer(
        "Какой твой любимый напиток? ☕️🍷", 
        reply_markup=kb_skip 
    )
    
    await state.set_state(Form.about)

@router.message(Form.about)
async def process_about(message: Message, state: FSMContext):
    about = message.text if message.text != "/skip" else "Пока ничего не рассказала"
    await state.update_data(about=about)
    # Теперь переходим к локации
    await message.answer("Где ты обычно бываешь? Поделись локацией, чтобы найти подруг рядом.", reply_markup=kb_geo)
    await state.set_state(Form.location)

@router.message(Form.location)
async def process_location(message: Message, state: FSMContext):
    if message.location:
        # Сохраняем широту и долготу отдельно
        await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
        await message.answer("Локация получена! 👌 Теперь пришли свое фото. 📸 Это обязательно!", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.photo)
    elif message.text == "/skip":
        await state.update_data(lat=None, lon=None)
        await message.answer("Пропускаем локацию. Пришли свое фото. 📸 Это обязательно!", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.photo)
    else:
        await message.answer("Пожалуйста, нажми на кнопку 'Отправить локацию' или напиши /skip")

@router.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    # Берем самое качественное фото из присланных
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    # --- ФИНАЛЬНЫЙ ШАГ: СОХРАНЕНИЕ В ОБЛАКО ---