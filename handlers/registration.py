from keyboards import kb_geo, kb_skip, main_kb, get_search_kb, show_main_menu
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
    # ВАЖНО: Всегда сбрасываем состояние
    await state.clear()
    
    # Убираем клавиатуру, если она была
    await message.answer(
        "Начинаем заполнение анкеты заново ✨",
        reply_markup=ReplyKeyboardRemove()
    )
    
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
        "Какое у тебя сегодня настроение?", 
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
    # Теперь переходим к локации
    await message.answer("Где ты обычно бываешь? Поделись локацией, чтобы найти подруг рядом.", reply_markup=kb_geo)
    await state.set_state(Form.location)

@router.message(Form.location)
async def process_location(message: Message, state: FSMContext):
    # Если пришла локация
    if message.location:
        # 1. Сразу меняем стейт, чтобы повторные нажатия не срабатывали
        await state.set_state(Form.photo) 
        
        # 2. Сохраняем координаты
        await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
        
        # 3. Отвечаем пользователю
        await message.answer(
            "Локация получена! Теперь пришли свое фото.🫧🕯️ Это обязательно!", 
            reply_markup=ReplyKeyboardRemove()
        )
        return # Выходим из функции

    elif message.text == "Пропустить":
        await state.set_state(Form.photo)
        await state.update_data(lat=None, lon=None)
        await message.answer("Пропускаем локацию. Пришли свое фото.", reply_markup=ReplyKeyboardRemove())
        return

# ... твой предыдущий код (process_location и т.д.)

@router.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    # 1. Берем фото и сохраняем его в состояние (как у тебя уже написано)
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
    
    # 5. Сбрасываем состояние, чтобы пользователь мог пользоваться кнопками меню
    await state.clear()

# Дополнительный хендлер для тех, кто пытается пропустить фото или прислать текст
@router.message(Form.photo)
async def process_photo_invalid(message: Message):
    await message.answer("Без фото нельзя! Это обязательно. Пожалуйста, пришли фотографию.")
    
    # --- ФИНАЛЬНЫЙ ШАГ: СОХРАНЕНИЕ В ОБЛАКО ---